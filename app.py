#!/usr/bin/env python3

import json
from flask import Flask
from flask import request
from flask import jsonify
from bot import Bot
app = Flask(__name__)

class GitlabBot(Bot):
    def __init__(self):
        try:
            self.authmsg = open('authmsg').read().strip()
        except:
            raise Exception("The authorization messsage file is invalid")

        super(GitlabBot, self).__init__()
        self.chats = {}
        try:
            chats = open('chats', 'r').read()
            self.chats = json.loads(chats)
        except:
            open('chats', 'w').write(json.dumps(self.chats))

        self.send_to_all('Hi !')

    def text_recv(self, txt, chatid):
        ''' registering chats '''
        txt = txt.strip()
        if txt.startswith('/'):
            txt = txt[1:]
        if txt == self.authmsg:
            if str(chatid) in self.chats:
                self.reply(chatid, "\U0001F60E  boy, you already got the power.")
            else:
                self.reply(chatid, "\U0001F60E  Ok boy, you got the power !")
                self.chats[chatid] = True
                open('chats', 'w').write(json.dumps(self.chats))
        elif txt == 'shutupbot':
            del self.chats[chatid]
            self.reply(chatid, "\U0001F63F Ok, take it easy\nbye.")
            open('chats', 'w').write(json.dumps(self.chats))
        else:
            self.reply(chatid, "\U0001F612 I won't talk to you.")

    def send_to_all(self, msg):
        for c in self.chats:
            self.reply(c, msg)


b = GitlabBot()


@app.route("/", methods=['GET', 'POST'])
def webhook():
    data = request.json
    # json contains an attribute that differenciates between the types, see
    # https://docs.gitlab.com/ce/user/project/integrations/webhooks.html
    # for more infos
    kind = data['object_kind']
    if kind == 'push':
        msg = generatePushMsg(data)
    elif kind == 'tag_push':
        msg = generatePushMsg(data)  # TODO:Make own function for this
    elif kind == 'issue':
        msg = generateIssueMsg(data)
    elif kind == 'note':
        msg = generateCommentMsg(data)
    elif kind == 'merge_request':
        msg = generateMergeRequestMsg(data)
    elif kind == 'wiki_page':
        msg = generateWikiMsg(data)
    elif kind == 'pipeline':
        msg = generatePipelineMsg(data)
    elif kind == 'build':
        msg = generateBuildMsg(data)
    b.send_to_all(msg)
    return jsonify({'status': 'ok'})

def generatePushMsg(data):
    msg = '{0} ({1})\n{2} new commits\n'\
        .format(getProjectTitle(data), data['project']['default_branch'], data['total_commits_count'])
    for commit in data['commits']:
        msg = msg + "[{0}]({1})\n{2}\n\n".format(commit['id'][:8], commit['url'].replace("_", "\_"), commit['message'].rstrip())
    return msg


def generateIssueMsg(data):
    action = data['object_attributes']['action']
    msg = "{0}\n{1} {2}\n{3}"\
        .format(getProjectTitle(data), action.capitalize(), getNewIssue(data), getBy(data))
    if action != 'close':
        msg = msg + "\n" + getAssignees(data)
    return msg

def generateCommentMsg(data):
    ntype = data['object_attributes']['noteable_type']
    if ntype == 'Commit':
        msg = 'note to commit'
    elif ntype == 'MergeRequest':
        msg = "{0}\nNote to {1}\n{2}\n---\n{3}"\
            .format(getProjectTitle(data), getMR(data), getBy(data), getNote(data))
    elif ntype == 'Issue':
        msg = "{0}\nNote to {1}\n{2}\n---\n{3}"\
            .format(getProjectTitle(data), getIssue(data), getBy(data), getNote(data))
    elif ntype == 'Snippet':
        msg = 'note on code snippet'
    return msg

def generateMergeRequestMsg(data):
    return "{0}\nNew {1}\n{2}\n{3}\n---\n{4}"\
        .format(getProjectTitle(data),getNewMR(data),getBy(data),getAssignee(data),getDescription(data))

def generateWikiMsg(data):
    return 'new wiki stuff'

def generatePipelineMsg(data):
    return 'new pipeline stuff'

def generateBuildMsg(data):
    return 'new build stuff'

def getProjectTitle(data):
    return "Project [{0}]({1})".format(data['project']['name'], data['project']['web_url'])

def getBy(data):
    return "by {0}".format(data['user']['name'])

def getIssue(data):
    return "issue [#{0}]({1}) {2}"\
        .format(data['issue']['iid'], data['object_attributes']['url'], data['issue']['title'])

def getNewIssue(data):
    return "issue [#{0}]({1}) {2}"\
        .format(data['object_attributes']['iid'], data['object_attributes']['url'], data['object_attributes']['title'])

def getMR(data):
    return "merge request [#{0}]({1}) {2}".format(data['merge_request']['iid'], data['object_attributes']['url'], data['merge_request']['title'])

def getNewMR(data):
    return "merge request [#{0}]({1}) {2}".format(data['object_attributes']['iid'], data['object_attributes']['url'], data['object_attributes']['title'])

def getNote(data):
    return data['object_attributes']['note']

def getDescription(data):
    return data['object_attributes']['description']

def getAssignees(data):
    assignees = ''
    for assignee in data.get('assignees', []):
        assignees += assignee['name'] + ' '
    return "Assignee on {0}".format(assignees)

def getAssignee(data):
    return "Assignee on {0}".format(data['object_attributes']['assignee']['name'])

if __name__ == "__main__":
    b.run_threaded()
    app.run(host='0.0.0.0', port=10111)
