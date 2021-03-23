#!/usr/bin/env python

import csv, codecs, os, types, re
import xlsxwriter.workbook

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from settings import *

import reports.models

from utilities.HeaderMerger import HeaderMerger
from utilities.moguraml import moguraml_to_null

from math import isinf, isnan

@xlsxwriter.worksheet.convert_cell_args
def write(self, row, col, *args):
        if not len(args):
            raise TypeError("write() takes at least 4 arguments (3 given)")

        token = args[0]

        if token is None:
            token = ''

        if self._is_supported_datetime(token):
            return self.write_datetime(row, col, *args)

        try:
	    if not isinf(float(token)) and not isnan(float(token)):
            	return self.write_number(row, col, *args)
        except ValueError:
            pass

        if token == '':
            return self.write_blank(row, col, *args)
        else:
            return self.write_string(row, col, *args)

def csv2xls(csv_filename, xls_filename, token = None):
	csv_file = open(csv_filename)
	r = csv.reader(csv_file)

	wb = xlsxwriter.workbook.Workbook(xls_filename)

	cell_format_title = wb.add_format({'bold': True,})
	cell_format_header = wb.add_format({'bold': True, 'fg_color': '#DDEEDD', 'align': 'center', 'border': 1,})
	cell_format_header_merged = wb.add_format({'bold': True, 'fg_color': '#DDEEDD', 'align': 'center', 'border': 1,})
	cell_format_data = wb.add_format({'left': 1, 'right': 1,})
	cell_format_data_footer = wb.add_format({'top': 1,})

	sheets = [] 
	ws = wb.add_worksheet()
	ws.write = types.MethodType(write, ws, xlsxwriter.worksheet.Worksheet)

	i = 0
	column_widths = {}
	titles = {}
	header_merger = HeaderMerger()
	sheet_info = {'sheet': ws, 'min_data_column': 0, 'max_data_column': 0, 'min_data_row': 0, 'max_data_row': 0}

	for row_index, row in enumerate(r):

		if len(row) == 0:
                        if len(titles) > 0:
                                ws.name = '-'.join([re.sub('[\/?*[\]]', '', x) for x in titles.values()])[:31]

			for key in column_widths.keys():
				ws.set_column(key, key, column_widths[key] + 3)

			for row, header in titles.items():
				ws.merge_range(row, 0, row, len(column_widths) - 1, header, cell_format_title)

			ws.write_row(i, 0, ['' for i in range(len(column_widths))], cell_format = cell_format_data_footer)

			headers = header_merger.merge()
						
			for i, header_row in headers.items():
				for j, header in header_row.items():	
					if header['rowspan'] > 1 or header['colspan'] > 1:
						ws.merge_range(i, j, i + header['rowspan'] - 1, j + header['colspan'] - 1, header['header'], cell_format_header_merged)

			sheets.append(sheet_info)

			ws = wb.add_worksheet()
			ws.write = types.MethodType(write, ws, xlsxwriter.worksheet.Worksheet)

			i = 0
			column_widths = {}
			titles = {}
			header_merger = HeaderMerger()
			sheet_info = {'sheet': ws, 'min_data_column': 0, 'max_data_column': 0, 'min_data_row': 0, 'max_data_row': 0}

			continue

		for key, cell in enumerate(row):
			row[key] = codecs.decode(cell, 'utf-8')

		if row[0][:1] == '\x7f':
			cell_format = cell_format_title
			titles[i] = row[0]
			ws.freeze_panes(i + 1, 0)
            	elif row[-1][-1:] == '\x7f':
			for key, cell in enumerate(row):
				column_widths[key] = max(column_widths[key] if key in column_widths else 0, len(row[key]))

			ws.freeze_panes(i + 1, 0)
                	row[-1] = row[-1][:-1]

			header_merger.upsert(i, row)

			ws.write_row(i, 0, row, cell_format_header)

			i += 1
			continue
		else:
			for key, cell in enumerate(row):
                                row[key] = moguraml_to_null(cell) 
				column_widths[key] = max(column_widths[key] if key in column_widths else 0, len(row[key]))

			sheet_info['min_data_row'] = min(i, sheet_info['min_data_row'] if 'min_data_row' in sheet_info else i)
			sheet_info['max_data_row'] = max(i, sheet_info['max_data_row'] if 'max_data_row' in sheet_info else i)
			sheet_info['max_data_column'] = max(len(row) - 1, sheet_info['max_data_column'] if 'max_data_column' in sheet_info else len(row) - 1)

			cell_format = cell_format_data

		ws.write_row(i, 0, row, cell_format)

		i += 1

        if len(titles) > 0:
                ws.name = '-'.join([re.sub('[\/?*[\]]', '', x) for x in titles.values()])[:31]

	for key in column_widths.keys():
		ws.set_column(key, key, column_widths[key] + 3)

	for row, header in titles.items():
		ws.merge_range(row, 0, row, len(column_widths) - 1, header, cell_format_title)

	ws.write_row(i, 0, ['' for i in range(len(column_widths))], cell_format = cell_format_data_footer)

	headers = header_merger.merge()

	for i, header_row in headers.items():
		for j, header in header_row.items():	
			if header['rowspan'] > 1 or header['colspan'] > 1:
				ws.merge_range(i, j, i + header['rowspan'] - 1, j + header['colspan'] - 1, header['header'], cell_format_header_merged)

	sheets.append(sheet_info)

	try:
		xls_charts_udf = reports.models.token.objects.get(token = token).report.xls_charts_udf.strip()
	except reports.models.token.DoesNotExist:
		pass
	else:
                if xls_charts_udf:		
                        exec xls_charts_udf

                        xls_charts_udf(wb, sheets)

	wb.close()
