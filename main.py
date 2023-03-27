import sys

from tlg_bot import bot

if __name__ == '__main__':
    # TODO Simplify
    argv = sys.argv
    if len(argv) == 5:
        d = {argv[1]: argv[2], argv[3]: argv[4]}
        if '-username' in d and '-password' in d:
            print(d['-username'], d['-password'])
            bot.start_bot(username=d['-username'], password=d['-password'])
    bot.start_bot()
