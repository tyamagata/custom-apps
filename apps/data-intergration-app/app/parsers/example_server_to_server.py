from app.parsers.exceptions import ParserException
from flask import current_app
from decimal import Decimal


class ExampleServerToServerParser:
    ad_id_col = 'FB Ad ID'
    fb_click_time_col = 'FB click time'
    event_time_col = 'Event time'
    conversion_col = 'Conversion type'
    actions_col = 'Actions'
    revenue_col = 'Revenue'

    def __init__(self, reader):
        self.reader = reader

    def to_s2s_events(self):
        events = []
        for row in self.reader:
            try:
                events.append({
                    'ad_id': row[self.ad_id_col],
                    # In the example CSV this is already a UNIX timestamp, most likely this is not the case in real
                    # life -> you need to do the translation
                    'fb_click_time': row[self.fb_click_time_col],
                    'event_time': row[self.event_time_col],
                    'type': row[self.conversion_col],
                    'actions': Decimal(row[self.actions_col]),
                    'value': Decimal(row[self.revenue_col])
                })

            except (IndexError, KeyError) as e:
                current_app.logger.error('Something went wrong: {}'.format(e))
                raise ParserException

        return events
