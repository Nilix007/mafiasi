from etherpad_lite import EtherpadLiteClient, EtherpadException
import time
from django.conf import settings

MIN_SESSION_REMAIN_TIME = 60*60*6
SESSION_DURATION = 60*60*12


class Etherpad(object):
    def __init__(self):
        self.api = EtherpadLiteClient(
            api_version='1.2.1',
            base_url="{0}://{1}/api/".format(
                settings.ETHERPAD_PROTOCOL,
                settings.ETHERPAD_DOMAIN),
            base_params={'apikey': settings.ETHERPAD_API_KEY})

    def _get_ep_user(self, user):
        return self.api.createAuthorIfNotExistsFor(
                authorMapper=user.id,
                name=user.username,
        )['authorID']

    def create_group_pad(self, group_name, pad_name):
        """
        Creates a Pad for Group
        """
        try:
            self.api.createGroupPad(
                groupID=self.get_group_id(group_name),
                padName=pad_name)
        except EtherpadException as e:
            # test if pad was already created, if so it's ok
            if e.message == "padName does already exist":
                return
            raise

    def create_session(self, user, group_name):
        group = self.get_group_id(group_name)
        user_ep = self._get_ep_user(user)
        # first we delete old sessions
        activ_sessions = self.api.listSessionsOfGroup(groupID=group)
        if activ_sessions:
            for sessionID, data in activ_sessions.items():
                if data['authorID'] == user_ep:
                    if data['validUntil'] > time.time() + MIN_SESSION_REMAIN_TIME:
                        # There is a valid session with over 6 hours
                        # remaining time
                        return
                    else:
                        # we delete the old Session so the user has not two
                        # on the same group. (technickal no problem,
                        # but the cookies will have more data
                        self.api.deleteSession(sessionID=sessionID)
        # we create a new session
        self.api.createSession(
                groupID = group,
                authorID = user_ep,
                validUntil = time.time() + SESSION_DURATION)

    def get_session_cookie(self, user):
        sessions = self.api.listSessionsOfAuthor(
                        authorID= self._get_ep_user(user)
                        )
        sessions_cookie = ','.join(sessions.keys())
        return sessions_cookie

    def get_group_id(self, group_name):
        return self.api.createGroupIfNotExistsFor(
                groupMapper=group_name
                )["groupID"]

    def get_group_pads(self, group_name):
        try:
            return self.api.listPads(groupID=self.get_group_id(group_name))['padIDs']
        except EtherpadException as e:
            if e.message == "groupID does not exist":
                # no pads for this group
                return []
            raise



