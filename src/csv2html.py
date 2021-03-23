# coding: utf-8

import csv, re, subprocess, StringIO 

from utilities.HeaderMerger import HeaderMerger
from utilities.moguraml     import moguraml_to_html

from django.utils.html      import escape

re_url = re.compile('(^|\s)(https?://\S+)(\s|$)')

def prepare_headers(header_merger, merge_headers):
	html = ''

	if not header_merger.columns_merged:
		headers = header_merger.merge_columns()
		if merge_headers:
			headers = header_merger.merge_rows()
		
		thead_set = False
	
		for header_row in headers.values(): 
			if not thead_set:
				html += '<thead>'
				thead_set = True

			html += '<tr class="csv-header header">'
			for header in header_row.values():
				header['header'] = re.sub(re_url, r'<a target="_blank" href="\2">\2</a>', header['header']) 
				html += '<td colspan="' + str(header['colspan']) + '" rowspan="' + str(header['rowspan']) + '" style="text-align:center;">' + header['header'] + '</td>'
			html += '</tr>\r\n'

		if thead_set:
			html += '</thead><tbody>'
		else:
			html += '<tbody>'

	return html

def csv2html(csvfile, limit = None, offset = 0, limit_per_table = None, merge_headers = False):

	reader = csv.reader(open(csvfile))
	
	rownum = 0
	table_rownum = 0

	if offset == 0:
		html = '<table class="tableinfo" style="width: 1px">\r\n'
	else:
		html = ''

	header_merger = HeaderMerger()
	
	for row in reader:
	    rownum += 1

	    if rownum <= offset:
	        continue

	    if limit:
	        if rownum > offset + limit:
	            break

	    if row == []:
		if table_rownum == 0:
			html += prepare_headers(header_merger, merge_headers)

		html += '</tbody></table><br/><table class="tableinfo" style="width: 1px">\r\n'
		table_rownum = 0

		header_merger = HeaderMerger()

	    elif row[0][:1] == '\x7f':
		html += '</tbody></table><h3>' + row[0][1:] + '</h3>\r\n<table class="tableinfo" style="width: 1px">\r\n'
	
	    elif row[-1][-1:] == '\x7f':
		row[-1] = row[-1][:-1]

		header_merger.upsert(rownum, row)	

	    else:
		html += prepare_headers(header_merger, merge_headers)

		table_rownum += 1

		if table_rownum <= limit_per_table if limit_per_table else table_rownum:
			colnum = 1
			if rownum % 2 == 0:
			    html += '<tr class="odd_row">\r\n'
			else:
			    html += '<tr class="even_row">\r\n'
		 
			for column in row:
                            column = moguraml_to_html(escape(column.decode('utf-8')).encode('utf-8'))
			    column = re.sub(re_url, r'<a target="_blank" href="\2">\2</a>', column) 
			    html += '<td class="column_' + str(colnum) + '">' + column + '</td>'
			    colnum += 1
			html += '</tr>\r\n'

		if limit_per_table and table_rownum == limit_per_table:
			if table_rownum % 10 == 1:
				inflections = {'shown': 'Показана ', 'records': ' запись'}
			elif 2 <= table_rownum % 10 <= 4:
				inflections = {'shown': 'Показаны ', 'records': ' записи'}
			else:
				inflections = {'shown': 'Показаны ', 'records': ' записей'}

	    		html += '<tr class="footer">\r\n<td colspan="100">' + inflections['shown'] + str(table_rownum) + inflections['records'] + '.</td>\r\n</tr>\r\n'

	html += prepare_headers(header_merger, merge_headers)	

	html += '</tbody></table>'
	
	return html
