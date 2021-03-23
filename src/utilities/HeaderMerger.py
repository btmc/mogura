import collections

class HeaderMerger(object):
	def __init__(self, headers = None):
		self.headers = collections.OrderedDict() 
		self.rows_merged = False
		self.columns_merged = False
		self.merged = False

		if headers:
			for rownum, header_row in headers.items():
				self.upsert(rownum, header_row)

	def upsert(self, rownum, header_row):
		if not rownum in self.headers:
			self.headers[int(rownum)] = {}

		if type(header_row) == list:
			header_row = {i:j for i,j in enumerate(header_row)}

		for colnum, header in header_row.items():
			self.headers[rownum][int(colnum)] = {'rowspan': header['rowspan'] if 'rowspan' in header else 1, 'colspan': header['colspan'] if 'colspan' in header else 1, 'header': (header['header'] if 'header' in header else header).strip()}

	def dump(self):
		return self.headers

	def merge_rows(self):
		if not self.rows_merged:
			for i, header_row in self.headers.items():
				for j, header in header_row.items():
					k = i
					while True:
						k += 1
						if k in self.headers and j in self.headers[k] and self.headers[k][j]['colspan'] == header['colspan'] and (self.headers[k][j]['header'] == header['header'] or self.headers[k][j]['header'] == ''):
							self.headers[i][j]['rowspan'] += 1
							del self.headers[k][j]
						else:
							break
		self.rows_merged = True

		return self.headers

	def merge_columns(self):
		if not self.columns_merged:
			for i, header_row in self.headers.items():
				for j, header in header_row.items():
					l = j
					while True:
						l += 1
						if j in self.headers[i] and l in self.headers[i] and (self.headers[i][l]['header'] == header['header'] or self.headers[i][l]['header'] == ''):
							self.headers[i][j]['colspan'] += 1
							del self.headers[i][l]
						else:
							break
		self.columns_merged = True

		return self.headers

	def merge(self):
		if not self.merged:
			self.merge_columns()
			self.merge_rows()
		self.merged = True

		return self.headers
