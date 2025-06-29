#
# BSD 3-Clause License
#
# Copyright (c) 2023, Fred W6BSD
# All rights reserved.
#

from .base import CallSelector


class Unsolicited(CallSelector):
    """Plugin for unsolicited calling opportunities"""

    def get(self, band):
        records = []
        for record in super().get(band):
            # Prioritize unsolicited opportunities over CQ calls
            if record.get('extra') == 'UNSOLICITED':
                # Give unsolicited calls higher priority (better SNR)
                record['snr'] += 5  # Boost SNR by 5 dB for unsolicited calls
            records.append(record)
        return self.select_record(records) 