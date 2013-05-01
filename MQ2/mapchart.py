#-*- coding: UTF-8 -*-

"""
 (c) 2011-2013 - Copyright Pierre-Yves Chibon

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

"""
MQ2 map chart generation from the data matrix.
"""

import logging

from MQ2 import read_input_file
from MQ2.qtl import QTL


LOG = logging.getLogger('MQ2')


def _extrac_qtl(peak, block):
    """ Given a row containing the peak of the QTL and all the rows of
    the linkage group of the said QTL (splitted per trait), determine
    the QTL interval and find the start and stop marker of the said
    interval.
    The interval is a LOD 2 interval.
    The approach is conservative in the way it takes the first and last
    marker within the interval.

    :arg peak, a list containing the row information for the peak marker
    :arg block, a list containing all the rows in the linkage group of
        this QTL, splitted per trait.

    """
    qtls = []
    if not peak:
        return qtls
    for trait in peak:
        threshold = 2
        # Search QTL start
        cnt = block.index(peak[trait])
        start = block[cnt]
        while cnt > 0:
            if block[cnt][-2] == trait:
                if (float(block[cnt][-1]) - float(threshold)) >= 0:
                    start = block[cnt]
            cnt = cnt - 1

        # Search QTL end
        end = []
        cnt = block.index(peak[trait])
        end = block[cnt]
        while cnt < len(block):
            if block[cnt][-2] == trait:
                if (float(block[cnt][-1]) - float(threshold)) >= 0:
                    end = block[cnt]
            cnt = cnt + 1

        qtl = QTL()
        qtl.trait = trait
        qtl.start_position = start[1]
        qtl.peak_start_position = peak[trait][1]
        qtl.peak_stop_position = peak[trait][1]
        qtl.stop_position = end[1]
        qtls.append(qtl)
    return qtls


def _order_linkage_group(group):
    """ For a given group (ie: a list containing [marker, position])
    order the list according to their position.
    """
    tmp = {}
    for row in group:
        if float(row[1]) in tmp:  # pragma: no cover
            tmp[float(row[1])].append(row[0])
        else:
            tmp[float(row[1])] = [row[0]]

    keys = list(tmp.keys())
    keys.sort()
    output = []
    for key in keys:
        for entry in tmp[key]:
            if not entry:
                continue
            output.append([entry, str(key)])
    return output


def generate_map_chart_file(qtl_matrix, lod_threshold,
                            map_chart_file='MapChart.map'):
    """ This function converts our QTL matrix file into a MapChart input
    file.

    :arg qtl_matrix: the path to the QTL matrix file generated by
        the plugin.
    :arg lod_threshold: threshold used to determine if a given LOD value
        is reflective the presence of a QTL.
    :kwarg map_chart_file: name of the output file containing the
        MapChart information.

    """

    qtl_matrix = read_input_file(qtl_matrix, sep=',')
    tmp_dic = {}
    cnt = 1
    tmp = {}
    block = []
    for row in qtl_matrix[1:]:
        linkgrp = qtl_matrix[cnt - 1][1]
        if cnt == 1:
            linkgrp = qtl_matrix[cnt][1]

        if not linkgrp in tmp_dic:
            tmp_dic[linkgrp] = [[], []]

        infos = row[1:4]
        if qtl_matrix[cnt][1] != linkgrp:
            qtls = _extrac_qtl(tmp, block)
            tmp_dic[linkgrp][1] = qtls
            linkgrp = qtl_matrix[cnt][1]
            tmp_dic[linkgrp] = [[], []]
            tmp = {}
            block = []

        tmp_dic[linkgrp][0].append([row[3], row[2]])

        colcnt = 4
        for cel in row[4:-1]:
            blockrow = infos[:]
            blockrow.extend([qtl_matrix[0][colcnt], cel])
            block.append(blockrow)
            if cel.strip() != '' and float(cel) >= float(lod_threshold):
                temp = infos[:]
                if not tmp:
                    temp.extend([qtl_matrix[0][colcnt], cel])
                    tmp[qtl_matrix[0][colcnt]] = temp
                elif (qtl_matrix[0][colcnt] in tmp
                      and float(cel) >= float(
                      tmp[qtl_matrix[0][colcnt]][-1])) \
                        or qtl_matrix[0][colcnt] not in tmp:
                    temp.extend([qtl_matrix[0][colcnt], cel])
                    tmp[qtl_matrix[0][colcnt]] = temp
            colcnt = colcnt + 1
        cnt = cnt + 1

    try:
        stream = open(map_chart_file, 'w')
        keys = list(tmp_dic.keys())
        ## Remove unknown group, reason:
        # The unlinked markers, if present, are always put in group U by
        # MapQTL. If you don't omit them and there are many (often), then
        # their names take so much space that it is difficult to fit them
        # on the page.
        if 'U' in keys:
            keys.remove('U')
        # Try to convert all the groups to float, which would result in
        # a better sorting. If that fails, fail silently.
        try:
            keys = [int(key) for key in keys]
        except ValueError:
            pass
        keys.sort()
        for key in keys:
            key = str(key)  # Needed since we might have converted them to int
            if tmp_dic[key]:
                if key == 'U':  # pragma: no cover
                    # We removed the key before, we should not be here
                    continue
                stream.write('group %s\n' % key)
                for entry in _order_linkage_group(tmp_dic[key][0]):
                    stream.write('  '.join(entry) + '\n')
                if tmp_dic[key][1]:
                    stream.write('\n')
                    stream.write('qtls\n')
                    for qtl in tmp_dic[key][1]:
                        stream.write('%s \n' % qtl.to_string())
                stream.write('\n')
                stream.write('\n')
    except IOError as err:  # pragma: no cover
        LOG.info('An error occured while writing the map chart map '
                 'to the file %s' % map_chart_file)
        LOG.debug("Error: %s" % err)
    finally:
        stream.close()
    LOG.info('Wrote MapChart map in file %s' % map_chart_file)
