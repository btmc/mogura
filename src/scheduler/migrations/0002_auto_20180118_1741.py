# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL \
            (
                sql = \
                    '''
                        create  function
                                    modifier_apply
                                        (
                                            i_datetime  timestamp,
                                            i_modifier  varchar(128)
                                        )
                        returns
                            timestamp
                        sql security
                            invoker
                        return
                            (
                                select
                                    case
                                        \r{}
                                    end
                                from
                                    (
                                        select
                                            substring_index
                                                (
                                                    i_modifier,
                                                    ' ',
                                                    1
                                                )   i_modifier_value,
                                            substring_index
                                                (
                                                    i_modifier,
                                                    ' ',
                                                    -1
                                                )   i_modifier_unit
                                    )   t1
                            )
                    '''.format \
                        (
                            ''.join \
                                (
                                    [
                                        '''\
                                            when
                                                i_modifier_unit
                                            regexp
                                                '^{0}s?$'
                                            then
                                                i_datetime
                                            +
                                                interval
                                                    i_modifier_value    {0}
                                      \r'''.format \
                                            (
                                                x
                                            )
                                        for
                                            x
                                        in
                                            [
                                                'month',    'day',
                                                'hour',     'minute',   'second'
                                            ]
                                    ]
                                )
                        ),
                reverse_sql = \
                    '''
                        drop    function
                                    modifier_apply
                    ''',
            )
    ]
