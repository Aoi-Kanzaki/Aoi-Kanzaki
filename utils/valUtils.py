import requests


class Region:
    """
    NA - North America

    EU - Europe

    BR - Brazil

    AP - Asia Pacific

    KR - Korea

    LATAM - Latin America
    """

    def __init__(self, region):
        self.region = region

    def requests(self):
        r = requests.get(
            f"https://valorant.secure.dyn.riotcdn.net/channels/public/x/status/{self.region.lower()}.json")
        if r.status_code == 200:
            json_data = r.json()
            return json_data
        else:
            return

    def get_status(self):

        json_data = self.requests()
        if not json_data['incidents'] and not json_data['maintenances']:
            return ({'issue': False, 'incidents': json_data['incidents'], 'maintenances': json_data['maintenances']})
        else:
            return ({'issue': True, 'incidents': json_data['incidents'], 'maintenances': json_data['maintenances']})

    def get_status_issue(self):
        """
        `self.get_status_issue()` would
        return either:
        True == There is an issue
        False == There is no issue
        """
        return self.get_status()['issue']

    def incidents_title(self):
        """to get the title of the incident:"""
        try:
            title = (self.get_status()["incidents"][0]['titles'][0]['content'])
            return title
        except IndexError:
            return

    def incidents_date(self):
        """to get the date of the incident:"""
        try:
            date = (self.get_status()['incidents'][0]
                    ['updates'][0]['created_at'][:10])
            return date
        except IndexError:
            return

    def incidents_reason(self):
        """to get the reason of the incident:"""
        try:
            message = (self.get_status()['incidents'][0]
                       ['updates'][0]['translations'][0]['content'])
            return message
        except IndexError:
            return

    def maintenances_title(self):
        """to get the title of the maintenance:"""
        try:

            title = (self.get_status()["maintenances"]
                     [0]['titles'][0]['content'])
            return title
        except IndexError:
            return

    def maintenances_date(self):
        """to get the date of the maintenance:"""
        try:

            date = (self.get_status()['maintenances']
                    [0]['updates'][0]['created_at'][:10])
            return date
        except IndexError:
            return

    def maintenances_reason(self):
        """to get the reason of the maintenance:"""
        try:
            message = (self.get_status()[
                       'maintenances'][0]['updates'][0]['translations'][0]['content'])
            return message
        except IndexError:
            return

    def maintenence_check(self):
        """
        `self.maintenence_check()`would return:
        True == There is an issue.

        **we are not doing False here
        since we already have a check for that
        via `self.get_issue()`**
        """
        if self.get_status()['maintenances'] != []:
            return True

    def incident_check(self):
        """
        `self.incident_check()`would return:
        True == There is an issue.

        **we are not doing False here
        since we already have a check for that
        via `self.get_issue()`**
        """
        if self.get_status()['incidents'] != []:
            return True
