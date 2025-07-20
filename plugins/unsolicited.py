#
# BSD 3-Clause License
#
# Copyright (c) 2023, Fred W6BSD
# All rights reserved.
#

from .base import CallSelector
import re


class Unsolicited(CallSelector):
    """Plugin for unsolicited calling opportunities"""

    def get(self, band):
        records = []
        wrap_re = re.compile(r'(RR73|73)$')
        for record in super().get(band):
            # ignore all non-unsolicited calls
            if record.get('extra') != 'UNSOLICITED':
                continue
            # only when wrapping up (RR73 or 73)
            msg = record.get('packet', {}).get('Message', '')
            if not wrap_re.search(msg):
                continue
            # boost wrap-up SNR
            record['snr'] += 5
            records.append(record)
        return self.select_record(records) 