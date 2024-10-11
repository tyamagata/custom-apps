from app.parsers.exceptions import ParserException
from flask import current_app


class ExampleAggregateS2SParser:
    platform_col = 'Platform'
    ad_unit_id_col = 'Ad Unit ID'
    event_name_col = 'Event Name'
    ad_interaction_time_col = 'Ad Interaction Time'
    event_time_col = 'Event Time'
    conversions_col = 'Conversions'
    value_col = 'Value'

    def __init__(self, reader):
        self.reader = reader

    def to_aggregate_multiplatform_s2s_events(self):
        events = []
        for row in self.reader:
            try:
                events.append({
                    'platform': row[self.platform_col],
                    'ad_unit_id': row[self.ad_unit_id_col],
                    # In the example CSV this is already a UNIX timestamp, most likely this is not the case in real
                    # life -> you need to do the translation
                    'ad_interaction_time': row[self.ad_interaction_time_col],
                    'event_time': row[self.event_time_col],
                    'event_name': row[self.event_name_col],
                    'conversions': row[self.conversions_col],
                    'value': row[self.value_col]
                })

            except (IndexError, KeyError) as e:
                current_app.logger.error(f'Something went wrong: {e}')
                raise ParserException

        return events
