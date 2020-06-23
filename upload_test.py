# -*- coding: utf-8 -*-
import os

from astgram.aliyunOSS import bucket, aliyunOSS_upload_file

if __name__ == '__main__':
    aliyunOSS_upload_file('/Users/WANGYISU/Desktop/xidian.jpg', 'xidian')
