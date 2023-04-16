
import argparse
from modules.constants import APP_VERSION


# ====================================================
# Argument parsing
# ====================================================
description = "Automates likes and comments on an instagram account or tag"
usage = "ilcbot.py [-h] [-u --username] [-p --password] [-t --target] [-le --loadenv] [-np NOOFPOSTS] [-ps TEXT] [-c FILE | -nc] [-d DELAY] [-hl --headless]"
examples="""
Examples:
ilcbot.py -u bob101 -p b@bpassw0rd1 -t elonmusk
ilcbot.py -u bob101 -p b@bpassw0rd1 -t elonmusk -np 20
ilcbot.py -u bob101 -p b@bpassw0rd1 -t '#haiku' -ps "Follow me @bob101" -c mycomments.txt
ilcbot.py -u bob101 -p b@bpassw0rd1 -t elonmusk --delay 5 --numofposts 30 --headless
ilcbot.py --loadenv --delay 5 --numofposts 10 --headless --nocomments
ilcbot.py -u bob101 -p b@bpassw0rd1 -t elonmusk --delay 5 --inlast 3M
ilcbot.py -u bob101 -p b@bpassw0rd1 -t elonmusk --delay 5,60
ilcbot.py -u bob101 -p b@bpassw0rd1 -t elonmusk --delay 10 -vs -ls
ilcbot.py -u bob101 -p b@bpassw0rd1 -t elonmusk --delay 10 -vs -ls 3 -cs 3
"""
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=description,
    usage=usage,
    epilog=examples,
    prog='ilcbot')


# optional arguments
parser.add_argument('-u','--username', metavar='', type=str, help='Instagram username')
parser.add_argument('-p','--password', metavar='', type=str, help='Instagram password')
parser.add_argument('-t', '--target',  metavar='', type=str, help='target (account or tag)')

parser.add_argument('-np', '--numofposts', type=int, metavar='', help='number of posts to like')
parser.add_argument('-ps', '--postscript', type=str, metavar='', help='additional text to add after every comment')
parser.add_argument('-ff', '--findfollowers', action='store_true', help="like/comment on posts from target's followers")
parser.add_argument('-fa', '--followersamount', type=int, metavar='', help='number of followers to process (default=all)', default=None)
parser.add_argument('-lc', '--likecomments', type=int, metavar='', help='like top n user comments per post')
parser.add_argument('-il', '--inlast', type=str, metavar='', help='target post within last n years (y), months (M), days (d), hours (h), mins (m), secs (s)')

parser.add_argument('-vs', '--viewstory', action='store_true', help='view stories')
parser.add_argument('-ls', '--likestory', type=int, nargs='?', help='like stories (default=all)', const=float('inf'))
parser.add_argument('-cs', '--commentstory', type=int, nargs='?', help='comments on stories (no comments if option not used)', const=float('inf'))
parser.add_argument('-os', '--onlystory', action='store_true', help='target only stories and not posts')

parser.add_argument('-mr', '--mostrecent', action='store_true', help='target most recent posts')
parser.add_argument('-rr', '--reloadrepeat', type=int, metavar='', help='reload the target n times (used with -mr)')

parser.add_argument('-mt', '--matchtags', type=str, metavar='', help='read tags to match from a file')
match_group = parser.add_mutually_exclusive_group()
match_group.add_argument('-mn', '--matchtagnum', type=int, metavar='', help='minimum tag match count for post to be qualified')
match_group.add_argument('-ma', '--matchalltags', action='store_true', help='match all tags in matchtags')

comments_group = parser.add_mutually_exclusive_group()
comments_group.add_argument('-c', '--comments', type=str, metavar='', help='file containing comments (one comment per line)')
comments_group.add_argument('-oc', '--onecomment', type=str, metavar='', help='specify only one comment')
comments_group.add_argument('-nc', '--nocomments', action='store_true', help='turn off comments')

parser.add_argument('-et', '--eltimeout',  type=str, metavar='', help='max time to wait for elements to be loaded (default=30)', default=30)
parser.add_argument('-d', '--delay', type=str, metavar='', help='time to wait during post switch default=(1,10)', default='1,10')
parser.add_argument('-br', '--browser',  type=str, metavar='', choices = ('chrome', 'firefox'), help='browser to use [chrome|firefox] (default=chrome)', default='chrome')
parser.add_argument('-hl', '--headless',  action='store_true', help='headless mode')
parser.add_argument('-le', '--loadenv',  action='store_true', help='load credentials from .env')
parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {APP_VERSION}')