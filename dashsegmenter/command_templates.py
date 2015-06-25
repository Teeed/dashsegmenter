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

import itertools

class CommandTemplate(object):
    def __init__(self, *command_template, **kwargs):
        super(CommandTemplate, self).__init__()
        self.command_template = list(command_template)
        self.inline = kwargs.get('inline', False)
        self.name = kwargs.get('name')

    def eval(self, definitions_dict):
        template = self.command_template
        evaluated = []

        for item in template:
            if isinstance(item, CommandTemplatePlaceholder):
                item = definitions_dict[item.name]
            
            if isinstance(item, CommandTemplate):
                item = item.eval(definitions_dict[item.name])

            if isinstance(item, list):
                evaluated.extend(item)
            else:
                evaluated.append(item)

        evaluated = itertools.imap(str, evaluated) # conversion to string
        evaluated = filter(lambda x: len(x) > 0, evaluated) # filter empty arguments (messes up packager)

        if self.inline:
            return ''.join(evaluated)


        return evaluated

class CommandTemplatePlaceholder(object):
    def __init__(self, name):
        super(CommandTemplatePlaceholder, self).__init__()
        self.name = name

FFMPEG_TEMPLATE = CommandTemplate('ffmpeg', '-re', '-i', CommandTemplatePlaceholder('INPUT_STREAM'), 
    CommandTemplatePlaceholder('OUTPUT_DEFINITIONS'))

FFMPEG_OUTPUT_DEFINITION_AUDIO = CommandTemplate(
    '-vn',
    '-c:a', CommandTemplatePlaceholder('AUDIO_CODEC'),
    '-ac', CommandTemplatePlaceholder('AUDIO_CHANNELS'),
    '-ab', CommandTemplatePlaceholder('AUDIO_BITRATE'),
    '-ar', CommandTemplatePlaceholder('AUDIO_SAMPLERATE'),
    '-f', CommandTemplatePlaceholder('STREAM_CONTAINER'),
    CommandTemplatePlaceholder('OUTPUT_STREAM')
    )

FFMPEG_OUTPUT_DEFINITION_VIDEO = CommandTemplate(
    '-an',
    '-s', CommandTemplatePlaceholder('DIMENSIONS'),
    '-c:v', CommandTemplatePlaceholder('VIDEO_CODEC'),
    '-r', CommandTemplatePlaceholder('FRAME_RATE'),
    '-g', CommandTemplatePlaceholder('I_FRAME_RATE'),
    '-preset', CommandTemplatePlaceholder('PRESET'),
    '-pix_fmt', CommandTemplatePlaceholder('PIXEL_FORMAT'),
    '-b:v', CommandTemplatePlaceholder('VIDEO_BITRATE'),
    # '-threads', CommandTemplatePlaceholder('ENCODING_THREADS'),
    '-f', CommandTemplatePlaceholder('STREAM_CONTAINER'),
    CommandTemplatePlaceholder('OUTPUT_STREAM')
    )

FFMPEG_OUTPUT_DEFINITION_VIDEO_THUMB_STREAMS = CommandTemplate(
    '[f=', CommandTemplatePlaceholder('STREAM_CONTAINER'), ']',
    CommandTemplatePlaceholder('OUTPUT_STREAM_0'),
    '|',
    '[f=', CommandTemplatePlaceholder('STREAM_CONTAINER'), ']',
    CommandTemplatePlaceholder('OUTPUT_STREAM_1'),
    inline=True,
    name='OUTPUT_STREAMS')
FFMPEG_OUTPUT_DEFINITION_VIDEO_CLONE = CommandTemplate(
    '-an',
    '-s', CommandTemplatePlaceholder('DIMENSIONS'),
    '-c:v', CommandTemplatePlaceholder('VIDEO_CODEC'),
    '-r', CommandTemplatePlaceholder('FRAME_RATE'),
    '-g', CommandTemplatePlaceholder('I_FRAME_RATE'),
    '-preset', CommandTemplatePlaceholder('PRESET'),
    '-pix_fmt', CommandTemplatePlaceholder('PIXEL_FORMAT'),
    '-b:v', CommandTemplatePlaceholder('VIDEO_BITRATE'),
    '-f', 'tee',
    '-map', '0:v',
    '-map', '0:a',
    FFMPEG_OUTPUT_DEFINITION_VIDEO_THUMB_STREAMS,
    )


FFMPEG_TEMPLATE_THUMBNAIL = CommandTemplate('ffmpeg', '-i', CommandTemplatePlaceholder('INPUT_STREAM'),
    '-ss', '00:00:01.000',
    '-vframes', '1',
    CommandTemplatePlaceholder('OUTPUT_FILE'))

PACKAGER_TEMPLATE = CommandTemplate('packager', CommandTemplatePlaceholder('STREAM_DEFINITIONS'),
    '--profile', CommandTemplatePlaceholder('PROFILE'),
    '--mpd_output', CommandTemplatePlaceholder('MPD_FILENAME'),
    CommandTemplate(
        '--segment_duration', '=', CommandTemplatePlaceholder('SEGMENT_DURATION'),
        inline=True,
        name='SEGMENT_DURATION_CONFIG'
    ),
    CommandTemplate(
        '--single_segment', '=', CommandTemplatePlaceholder('SINGLE_SEGMENT'),
        inline=True,
        name='SINGLE_SEGMENT_CONFIG'
    ))

PACKAGER_STREAM_DEFINITION = CommandTemplate(
    'input=', CommandTemplatePlaceholder('INPUT_STREAM_ADDRESS'), ',',
    'stream=', CommandTemplatePlaceholder('STREAM_TYPE'), ',',
    'init_segment=', CommandTemplatePlaceholder('INIT_SEGMENT_NAME'), ',',
    'segment_template=', CommandTemplatePlaceholder('SEGMENT_TEMPLATE'), ',',
    'bandwidth=', CommandTemplatePlaceholder('BITRATE'),
    inline=True)
