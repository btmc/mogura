#!/usr/bin/env python

import re, itertools

class AbstractNode(object):
	def is_meta(self):
		return self.sub_nodes() != None

	def sub_nodes(self):
		raise NotImplementedError()


class RealNode(AbstractNode):
	pass


class RegexpNode(AbstractNode):
	def __init__(self, sql, *args, **kwargs):
		self.match = re.match(self.re, sql.strip(), re.S)
		
		if self.match == None:
			raise TypeError()

		self.sql = self.match.groupdict()['body']

	def peer_nodes(self):
		return [UnknownNode(self.match.groupdict()['pre']), self, UnknownNode(self.match.groupdict()['post'])] 


class SimpleNode(RegexpNode, RealNode):
	def __init__(self, sql, *args, **kwargs):
		self.re = '(?P<pre>)(?P<body>.*)(?P<post>)'

		for CheckNode in RealNode.__subclasses__():
			if CheckNode == self.__class__:
				continue

			try:
				CheckNode(sql)
			except TypeError:
				pass
			else:
				raise TypeError()

		super(self.__class__, self).__init__(sql, *args, **kwargs)

	def sub_nodes(self):
		return None


class ParallelNode(RegexpNode, RealNode):
	def __init__(self, sql, *args, **kwargs):
		self.re = '(?P<pre>.*?)(?P<body>--==(?P<key>[^=]*)start==--(?P<inner_body>.*)--==(?P=key)finish==--)(?P<post>.*)'

		super(self.__class__, self).__init__(sql, *args, **kwargs)

	def sub_nodes(self):	
		for sql in self.match.groupdict()['inner_body'].split('\r\n--==%snext==--\r\n' % self.match.groupdict()['key']):
                        if sql.strip():
                                yield UnknownNode(sql.strip())


class MultipleNode(RegexpNode, RealNode):
	def __init__(self, sql, *args, **kwargs):
		self.re = '(?P<pre>.*?)(?P<body>--=(?P<key>[^=]*)start=--(?P<inner_body>.*)--=(?P=key)finish=--)(?P<post>.*)'

		super(self.__class__, self).__init__(sql, *args, **kwargs)

	def sub_nodes(self):
		def get_step(match):
			try:
				return int(re.search('/\*=%sstep\s+(?P<step>[0-9]+?)\s*=\*/' % match.groupdict()['key'], self.sql).groupdict()['step'])
			except:
				return 1

		re_range = '/\*=(?P<key>.*?)from=\*/\s*(?P<from>[0-9]+)\s*/\*=endfrom=\*/(?P<inner_body>.*?)/\*=(?P=key)to=\*/\s*(?P<to>[0-9]+)\s*/\*=endto=\*/'
		range_match = re.search(re_range, self.sql, re.S)

		if range_match != None:
			i = int(range_match.groupdict()['from'])
			i_to = int(range_match.groupdict()['to'])
			i_step = get_step(range_match)

			while i < i_to:
				for sub_node in UnknownNode(re.sub(re_range, '%s\g<inner_body>%s' % (str(i), str(min(i + i_step, i_to)),), self.sql, re.S)).sub_nodes():
					yield sub_node

				i += i_step

			raise StopIteration

		re_enum = '/\*=(?P<key>.*?)in=\*/\s*(?P<in>.+?)\s*/\*=endin=\*/'
		enum_match = re.search(re_enum, self.sql, re.S)

		if enum_match != None:
			i_enum = enum_match.groupdict()['in'].split(',')	
			i_step = get_step(enum_match)

			i = 0
			while i < len(i_enum):
				for sub_node in UnknownNode(re.sub(re_enum, ','.join(i_enum[i:i + i_step]).strip(), self.sql, re.S)).sub_nodes():
					yield sub_node

				i += i_step

			raise StopIteration

		for sub_node in UnknownNode(self.match.groupdict()['inner_body']).sub_nodes():
			yield sub_node


class UnknownNode(AbstractNode):
	def __init__(self, sql, *args, **kwargs):
		self.sql = sql.strip()

	def sub_nodes(self):
		if not self.sql:
			raise StopIteration

		candidate_nodes = []	

		for CandidateNode in RealNode.__subclasses__():
			try:
				candidate_nodes += [CandidateNode(self.sql)]
			except:
				pass

		candidate_nodes.sort(key=lambda x: len(x.sql), reverse=True)

		for sub_node in candidate_nodes[0].peer_nodes():
			if type(sub_node) == self.__class__:
				for sub_sub_node in sub_node.sub_nodes():
					yield sub_sub_node 
			else:
				yield sub_node 
