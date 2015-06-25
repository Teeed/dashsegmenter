# -*- coding: utf-8 -*-

# This file is part of dashsegmenter project
# http://github.com/Teeed/dashsegmenter
#
# The MIT License (MIT)
# 
# Copyright (c) 2014 Tadeusz Magura-Witkowski
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from subprocess import Popen
from multiprocessing import Value
from time import sleep
import os
import sys
import signal
import ctypes
import itertools
import errno


import internal_settings
import command_templates

ignored_pid = Value('l')

# exit app when some of my children has died
# it will result in killing all remaining children and commiting suicide at the end
# pretty nice story huh? :)
def child_exit_handler(signal, frame_object):
    global ignored_pid
    pid, _whatever = os.waitpid(-1, 0)

    if pid == ignored_pid.value:
        return

    sys.exit(1)
signal.signal(signal.SIGCHLD, child_exit_handler)

class Settings(object):
    def __init__(self, base_port, chunk_interval, thumbnail_interval, thumbnail_stream, input_stream, output_path,
        debug_ffmpeg=False, debug_packager=False, debug_thumbnail=False):
        super(Settings, self).__init__()
        self.base_port = base_port
        self.chunk_interval = chunk_interval
        self.input_stream = input_stream
        self.output_path = output_path
        self.thumbnail_interval = thumbnail_interval
        self.thumbnail_stream = thumbnail_stream
        self.debug_packager = debug_packager
        self.debug_ffmpeg = debug_ffmpeg
        self.debug_thumbnail = debug_thumbnail

        if thumbnail_stream != None:
            thumbnail_stream.is_thumbnail_source = True

class Stream(object):
    def __init__(self, name, bitrate, port=None):
        super(Stream, self).__init__()
        self.name = name
        self.bitrate = bitrate
        self.port = port

    def __eq__(self, other):
        return self.name == other.name and self.__class__ == other.__class__

    @property
    def output_address(self):
        return internal_settings.STREAM_ADDRESS_INPUT % {'address': '127.0.0.1', 'port': self.port}

    input_address = output_address

    @property
    def output_address_thumbnail(self):
        return internal_settings.STREAM_ADDRESS_INPUT % {'address': '127.0.0.1', 'port': self.port_thumb}

    @property 
    def bitrate_in_k(self):
        return '%sk' % (int(self.bitrate/1000))

    @property 
    def init_segment_name(self):
        if isinstance(self, AudioStream):
            return internal_settings.INIT_SEGMENT_NAME_AUDIO % (self.name)

        return internal_settings.INIT_SEGMENT_NAME_VIDEO % (self.name)

    @property
    def segment_template(self):
        if isinstance(self, AudioStream):
            return internal_settings.SEGMENT_TEMPLATE_AUDIO % (self.name)

        return internal_settings.SEGMENT_TEMPLATE_VIDEO % (self.name)

    @property
    def stream_type(self):
        return 'audio' if isinstance(self, AudioStream) else 'video'

    @property
    def packager_definition(self):
        values = {
            'INPUT_STREAM_ADDRESS': self.input_address,
            'STREAM_TYPE': self.stream_type,
            'INIT_SEGMENT_NAME': self.init_segment_name,
            'SEGMENT_TEMPLATE': self.segment_template,
            'BITRATE': self.bitrate,
        }
        
        return command_templates.PACKAGER_STREAM_DEFINITION.eval(values)

class AudioStream(Stream):
    @property
    def ffmpeg_definition(self):
        values = {
            'AUDIO_CODEC': internal_settings.AUDIO_CODEC,
            'AUDIO_CHANNELS': internal_settings.AUDIO_CHANNELS,
            'AUDIO_BITRATE': self.bitrate_in_k,
            'AUDIO_SAMPLERATE': internal_settings.AUDIO_SAMPLERATE,
            'STREAM_CONTAINER': internal_settings.STREAM_CONTAINER,
            'OUTPUT_STREAM': self.output_address
        }
        
        return command_templates.FFMPEG_OUTPUT_DEFINITION_AUDIO.eval(values)

class VideoStream(Stream):
    @property
    def dimensions(self):
        return '%sx%s' % (self.width, self.height)

    def __init__(self, name, bitrate, width, height, frame_rate, i_frame_rate=None, port=None, disable_packager=False):
        super(VideoStream, self).__init__(name, bitrate, port)

        self.width = width
        self.height = height
        self.frame_rate = frame_rate
        self.i_frame_rate = i_frame_rate
        self.is_thumbnail_source = False
        self.disable_packager = disable_packager

    @property
    def ffmpeg_definition(self):
        if self.is_thumbnail_source:
            values = {
                'DIMENSIONS': self.dimensions,
                'VIDEO_CODEC': internal_settings.VIDEO_CODEC,
                'FRAME_RATE': self.frame_rate,
                'I_FRAME_RATE': self.i_frame_rate,
                'PRESET': internal_settings.VIDEO_PRESET,
                'PIXEL_FORMAT': internal_settings.PIXEL_FORMAT,
                'VIDEO_BITRATE': self.bitrate,              
                'OUTPUT_STREAMS': 
                {
                    'STREAM_CONTAINER': internal_settings.STREAM_CONTAINER,
                    'OUTPUT_STREAM_0': self.output_address,
                    'OUTPUT_STREAM_1': self.output_address_thumbnail,
                }
            }
            
            return command_templates.FFMPEG_OUTPUT_DEFINITION_VIDEO_CLONE.eval(values)
        else:
            values = {
                'DIMENSIONS': self.dimensions,
                'VIDEO_CODEC': internal_settings.VIDEO_CODEC,
                'FRAME_RATE': self.frame_rate,
                'I_FRAME_RATE': self.i_frame_rate,
                'PRESET': internal_settings.VIDEO_PRESET,
                'PIXEL_FORMAT': internal_settings.PIXEL_FORMAT,
                'VIDEO_BITRATE': self.bitrate,
                'STREAM_CONTAINER': internal_settings.STREAM_CONTAINER,
                'OUTPUT_STREAM': self.output_address,
            }
            
            return command_templates.FFMPEG_OUTPUT_DEFINITION_VIDEO.eval(values)

    @property
    def packager_definition(self):
        if self.disable_packager:
            return ''
        else:
            return super(VideoStream, self).packager_definition

class StreamNameDuplicated(Exception):
    pass

class InvalidThumbnailStream(Exception):
    pass

class NoStreams(Exception):
    pass


DEVNULL = open(os.devnull, 'w')

libc = ctypes.CDLL("libc.so.6")
def set_pdeathsig(sig=signal.SIGTERM):
    def callable():
        return libc.prctl(1, sig) # PR_SET_PDEATHSIG @ http://man7.org/linux/man-pages/man2/prctl.2.html
    return callable

class StreamsController(object):
    def __init__(self, settings):
        super(StreamsController, self).__init__()
        self.settings = settings
        self._streams = set([])

        self._commandline_ffmpeg = None
        self._commandline_packager = None
        self._commandline_thumbgen = None

        if settings.thumbnail_stream != None and not isinstance(settings.thumbnail_stream, VideoStream):
            raise InvalidThumbnailStream('thumbnail_stream should be a VideoStream')

    def add_stream(self, stream):
        # check if we have duplicated stream names..
        identical_streams = any(itertools.ifilter(lambda x: x == stream, self._streams))

        if identical_streams:
            raise StreamNameDuplicated()

        self._streams.add(stream)

    def _assign_ports(self):
        port = self.settings.base_port

        base_port, port = port, port+1

        for stream in self._streams:
            stream.port = port

            if isinstance(stream, VideoStream) and stream.is_thumbnail_source:
                port += 1

                stream.port_thumb = port

            port += 1
    
    def _build_commandlines(self):
        if len(self._streams) == 0:
            raise NoStreams()

        ffmpeg_stream_definitions = []
        packager_stream_definitions = []
        self._commandline_thumbgen = None
        self._commandline_packager = None

        for stream in self._streams:
            ffmpeg_stream_definitions.extend(stream.ffmpeg_definition)
            packager_stream_definitions.append(stream.packager_definition)

        values = {
            'INPUT_STREAM': self.settings.input_stream,
            'OUTPUT_DEFINITIONS': ffmpeg_stream_definitions,
        }
        self._commandline_ffmpeg = command_templates.FFMPEG_TEMPLATE.eval(values)

        values = {
            'STREAM_DEFINITIONS': packager_stream_definitions,
            'PROFILE': internal_settings.DASH_PROFILE,
            'MPD_FILENAME': internal_settings.MPD_FILENAME,
            'SEGMENT_DURATION_CONFIG': {
                'SEGMENT_DURATION': self.settings.chunk_interval,
            },
            'SINGLE_SEGMENT_CONFIG': {
                'SINGLE_SEGMENT': internal_settings.SINGLE_SEGMENT,
            }
        }
        if len(packager_stream_definitions) > 0:
            self._commandline_packager = command_templates.PACKAGER_TEMPLATE.eval(values)


        if self.settings.thumbnail_stream != None:
            self._commandline_thumbgen = []

            values = {
                'INPUT_STREAM': self.settings.thumbnail_stream.output_address_thumbnail,
                'OUTPUT_FILE': internal_settings.THUMBNAIL_TEMPORARY_FILENAME 
            }
            self._commandline_thumbgen = command_templates.FFMPEG_TEMPLATE_THUMBNAIL.eval(values)


    def _move_thumbnail(self):
        try:
            os.unlink(os.path.join(self.settings.output_path, internal_settings.THUMBNAIL_FILENAME))
        except OSError:
            pass

        try:
            os.rename(os.path.join(self.settings.output_path, internal_settings.THUMBNAIL_TEMPORARY_FILENAME), os.path.join(self.settings.output_path, internal_settings.THUMBNAIL_FILENAME))
        except OSError as e:
            print 'Cannot replace thumbnail:', e


    def _generate_thumbnail(self):
        # check if needed
        if self._commandline_thumbgen == None:
            return


        try:
            os.unlink(os.path.join(self.settings.output_path, internal_settings.THUMBNAIL_TEMPORARY_FILENAME))
        except OSError:
            pass

        def preexec_fun():
            ignored_pid.value = os.getpid()
            set_pdeathsig(signal.SIGKILL)()


        def pid_exists(pid):
            """Check whether pid exists in the current process table.
            UNIX only.
            """
            if pid < 0:
                return False
            if pid == 0:
                # According to "man 2 kill" PID 0 refers to every process
                # in the process group of the calling process.
                # On certain systems 0 is a valid PID but we have no way
                # to know that in a portable fashion.
                raise ValueError('invalid PID 0')
            try:
                os.kill(pid, 0)
            except OSError as err:
                if err.errno == errno.ESRCH:
                    # ESRCH == No such process
                    return False
                elif err.errno == errno.EPERM:
                    # EPERM clearly means there's a process to deny access to
                    return True
                else:
                    # According to "man 2 kill" possible error values are
                    # (EINVAL, EPERM, ESRCH)
                    raise
            else:
                return True

        kwargs = {'cwd': self.settings.output_path, 'close_fds': True, 'preexec_fn': preexec_fun}
        if self.settings.debug_thumbnail:
            print 'Thumbnail command:', self._commandline_thumbgen
        else:
            kwargs.update({'stdout':DEVNULL, 'stderr': DEVNULL})

        # we will generate thumbnail with max waiting time 30s
        thumbnail_generator = Popen(self._commandline_thumbgen, **kwargs)

        count = 30
        while count > 0:
            sleep(1)

            # there is bug in poll() :(
            # so we have to do basic pid checking

            pool_result = pid_exists(thumbnail_generator.pid)

            # pool_result = thumbnail_generator.poll()

            if self.settings.debug_thumbnail:
                print 'Thumbnail code:', pool_result

            if not pool_result:
                self._move_thumbnail()
                return
            
            count -= 1

        try:
            thumbnail_generator.terminate()
        except OSError:
            pass


    def run(self):
        self._assign_ports()
        self._build_commandlines()

        KWARGS_ARGS_BASE = {'cwd': self.settings.output_path, 'preexec_fn': set_pdeathsig(signal.SIGKILL)}
        KWARGS_ARGS_NORMAL = {'stdout': DEVNULL, 'stderr': DEVNULL}

        KWARGS_FFMPEG, KWARGS_PACKAGER = KWARGS_ARGS_BASE.copy(), KWARGS_ARGS_BASE.copy()

        if self.settings.debug_ffmpeg:
            print 'FFmpeg commandline:', self._commandline_ffmpeg
        else:
            KWARGS_FFMPEG.update(KWARGS_ARGS_NORMAL)


        # start ffmpeg (media converter)
        try:
            ffmpeg = Popen(self._commandline_ffmpeg, **KWARGS_FFMPEG)
        except OSError as e:
            print 'Cannot start ffmpeg: %s' % str(e)

            sys.exit(1)

        # start packager (segmenter)
        if self._commandline_packager:
            if self.settings.debug_packager:
                print 'Packager commandline:', self._commandline_packager
            else:
                KWARGS_PACKAGER.update(KWARGS_ARGS_NORMAL)

            try:
                packager = Popen(self._commandline_packager, **KWARGS_PACKAGER)
            except OSError as e:
                print 'Cannot start packager (did you run autoinstall.sh script?): %s' % str(e)

                sys.exit(1)


        # it never returns, will be killed with child_exit_handler or my process will be killed :<
        # so, we can do thumbnail creation here in rather ugly way (timings wont be accurate)
        while True:
            sleep(self.settings.thumbnail_interval)
            self._generate_thumbnail()
            