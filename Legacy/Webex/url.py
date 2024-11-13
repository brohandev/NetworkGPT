# [WEBEX]
# WEBEX API URLs
WEBEX_BASE_URL = 'https://webexapis.com/v1'
WEBEX_ROOMS_URI = '/rooms'  # GET list of rooms that caller is a participant in
CREATE_WEBEX_WEBOOK_URI = '/webhooks'  # POST new webhook
UPDATE_WEBEX_WEBOOK_URI = '/webhooks/{webhook_id}'  # PUT new webhook
WEBEX_MESSAGE_CONTENT_URI = '/messages/{message_id}'  # GET text content in message
