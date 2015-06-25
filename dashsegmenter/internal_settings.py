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

# internal project tweaks
# change at your own risk!

STREAM_CONTAINER = 'mpegts'

STREAM_ADDRESS_INPUT = 'udp://%(address)s:%(port)s'
STREAM_ADDRESS_OUTPUT = 'udp://%(address)s:%(port)s'

AUDIO_CODEC = 'libfdk_aac'
AUDIO_CHANNELS = '2'
AUDIO_SAMPLERATE = '44100'

VIDEO_CODEC = 'libx264'
VIDEO_PRESET = 'fast'
PIXEL_FORMAT = 'yuv420p'

DASH_PROFILE = 'live'
MPD_FILENAME = 'manifest.mpd'
THUMB_FILENAME = 'thumbnail.png'
SINGLE_SEGMENT = 'false'

# audio and video file names must be different!
INIT_SEGMENT_NAME_AUDIO = '%s_init_a.mp4'
INIT_SEGMENT_NAME_VIDEO = '%s_init_v.mp4'
SEGMENT_TEMPLATE_AUDIO = '%s_$Number$_a.mp4'
SEGMENT_TEMPLATE_VIDEO = '%s_$Number$_v.mp4'
THUMBNAIL_FILENAME = 'thumbnail.png'
THUMBNAIL_TEMPORARY_FILENAME = '.thumbnail.png'

STARTING_PORT_NUMBER = 10000
PORT_INCREMENT = 100
