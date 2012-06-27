#-*- coding: UTF-8 -*-

"""
 (c) Copyright Pierre-Yves Chibon -- 2011, 2012

 Distributed under License GPLv3 or later
 You can find a copy of this license on the website
 http://www.gnu.org/licenses/gpl.html

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
 MA 02110-1301, USA.
"""


import datetime
import logging
import os
import tarfile
import tempfile
import zipfile

log = logging.getLogger('pymq2')



def set_tmp_folder():
    """ Create a temporary folder using the current time in which
    the zip can be extracted and which should be destroyed afterward.
    """
    output = "%s" % datetime.datetime.now()
    output = output.rsplit('.', 1)[0].strip()
    for char in [' ', ':', '.', '-']:
        output = output.replace(char, '')
    output.strip()
    tempfile.tempdir = '%s/%s' % (tempfile.gettempdir(), output)
    return tempfile.gettempdir()



def extract_zip(filename):
    """ Extract the sources in a temporary folder.
    :arg filename, name of the zip file containing the data from MapQTL
    which will be extracted
    """
    extract_dir = tempfile.gettempdir()
    log.info("Extracting %s in %s " % (filename, extract_dir))
    if not os.path.exists(extract_dir):
        try:
            os.mkdir(extract_dir)
        except IOError, err:
            log.info("Could not generate the folder %s" % extract_dir)
            log.debug("Error: %s" % err)

    if zipfile.is_zipfile(filename):
        try:
            zfile = zipfile.ZipFile(filename, "r")
            zfile.extractall(extract_dir)
            zfile.close()
        except Exception, err:
            log.debug("Error: %s" % err)
    else:
        try:
            tar = tarfile.open(filename)
            tar.extractall(extract_dir)
            tar.close()
        except tarfile.ReadError, err:
            log.debug("Error: %s" % err)

    return extract_dir


def read_input_file(filename, sep='\t'):
    """Reads a given inputfile (tab delimited) and returns a matrix
    (list of list).
    arg: filename, the complete path to the inputfile to read
    """
    output = []
    stream = None
    try:
        stream = open(filename, 'r')
        for row in stream:
            output.append(row.strip().split(sep))
    except Exception, err:
        log.info("Something wrong happend while reading the file %s " % filename)
        log.debug("ERROR: %s" % err)
    finally:
        if stream:
            stream.close()
    return output


class MQ2Exception(Exception):
    """ Basic exception class to be used by the pymq2 library. """
    pass
    