# coding: utf-8

from django import template

from django.utils.safestring import mark_safe

from collections import Mapping

class SafeContext(template.Context):

    def __init__(self, *args, **kwargs):

        if len(args) > 0:
                dict_ = args[0]
        elif 'dict_' in kwargs:
                dict_ = kwargs['dict_']

        if isinstance(dict_, Mapping):
            for i in dict_:
                    if isinstance(dict_[i], basestring):
                            dict_[i] = mark_safe(dict_[i])

        super(SafeContext, self).__init__(*args, **kwargs)
