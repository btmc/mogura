import re, string

mogura_tag = re.compile('(?P<tag>\[~(?P<closing>/)?mogura:html:(?P<name>.+?)(~(?P<params>[^\[\]]*?))?~\])')

def listed(function):
        return lambda value: [function(item) for item in value] if type(value) == list else function(value)

@listed
def moguraml_to_html(value):
        for tag in re.finditer(mogura_tag, value): 
                value = value.replace(tag.groupdict()['tag'], '<%(closing)s%(name)s %(params)s>' % {i:j.translate(string.maketrans('#`', '&"')) for i,j in tag.groupdict('').iteritems()})

        return value

@listed
def moguraml_to_null(value):
        for tag in re.finditer(mogura_tag, value): 
                value = value.replace(tag.groupdict()['tag'], '')

        return value
