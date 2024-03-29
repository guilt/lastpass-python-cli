#!/usr/bin/env python

"""
LastPass CLI in Python. Very Minimal.
---------------------------------------------
  lpass {--help}

  lpass login
      [--trust]
      [--plaintext-key [--force, -f]]
      [--color=auto|never|always]
      USERNAME

  lpass logout
      [--force, -f]
      [--color=auto|never|always]

  lpass show
      [--sync=auto|now|no]
      [--clip, -c]
      [--quiet, -q]
      [--expand-multi, -x]
      [--json, -j]
      [--all|--username|--password|--url|--notes|--field=FIELD|--id|--name|--attach=ATTACH]
      [--basic-regexp, -G|--fixed-strings, -F]
      [--color=auto|never|always]
      UNIQUE

  lpass ls
      [--sync=auto|now|no]
      [--long, -l]
      [-m]
      [-u]
      [--color=auto|never|always]
      [GROUP]
---------------------------------------------
"""

from __future__ import print_function
import argparse
import getpass
import json
import os
import sys

from operator import attrgetter

try:
    import lastpass
    from lastpass.parser import b64encode, b64decode
except ImportError:
    print('Ensure you install lastpass-python.', file=sys.stderr)
    sys.exit(1)

try:
    import colorama
    colorama.init()
    OUTPUT_COLOR = 'auto'
except ImportError:
    OUTPUT_COLOR = 'never'

S_RED = '\033[31m'
S_BLUE = '\033[34m'
S_GREEN = '\033[32m'
S_CYAN = '\033[36m'
S_MAGENTA = '\033[35m'
S_YELLOW = '\033[33m'
S_WHITE = '\033[37m'
S_RESET = '\033[0m'

LPASS_CONFIG_FILE = os.getenv('LPASS_CONFIG_FILE', os.path.expanduser("~/.lpass-config"))
LPASS_BLOB_FILE = os.getenv('LPASS_BLOB_FILE', os.path.expanduser("~/.lpass-blob"))
CLIENT_ID = None  # Usually the IMEI.


def __colored(message, color, file_=sys.stdout):
    output_color = False
    if OUTPUT_COLOR == 'never':
        pass
    elif OUTPUT_COLOR == 'auto':
        output_color = file_.isatty()
    elif OUTPUT_COLOR == 'always':
        output_color = True
    if output_color:
        return '{}{}{}'.format(color, message, S_RESET)
    return message


def __print_message(message, color=S_WHITE, file_=sys.stdout):
    print(__colored(message, color, file_=file_), file=file_)


def __print_error(message, file_=sys.stderr):
    print(__colored(message, S_RED, file_=file_), file=file_)


def __write_config(username=None, password=None, mfa=False):
    with open(LPASS_CONFIG_FILE, 'w') as writable_config:
        data = {'username': username, 'mfa': mfa}
        if password:
            __print_message('Writing Passwords to Configuration is not Recommended.')
            data['password']: b64encode(str.encode(password)).decode()
        writable_config.write(json.dumps(data))


def __read_config():
    if not os.path.exists(LPASS_CONFIG_FILE):
        raise Exception('Unable to Get Configuration.')
    with open(LPASS_CONFIG_FILE) as readable_config:
        data = json.loads(readable_config.read())
        (username, password, mfa) = (data.get('username'), b64decode(data.get('password', '')).decode(), data.get('mfa', False))
        return username, password, mfa


def __get_login(username, password, mfa):
    if not username:
        raise ValueError('No Username. Please Login.')
    if not password:
        password = getpass.getpass('Please Enter Lastpass Password for User {}: '.format(username))
    if not password:
        raise ValueError('Empty Password.')
    if mfa:
        mfa = getpass.getpass('Please Enter Lastpass MFA Password for User {}: '.format(username))
        if not mfa:
            raise ValueError('Empty MFA Password.')
    else:
        mfa = None
    if os.path.exists(LPASS_BLOB_FILE):
        vault = lastpass.Vault.open_local(LPASS_BLOB_FILE, username, password)
    else:
        vault = lastpass.Vault.open_remote(username, password, mfa, CLIENT_ID, blob_filename=LPASS_BLOB_FILE)
    return vault, password


def command_login(args):
    """lpass login Commandlet"""
    if not args.plaintext_key:
        raise NotImplementedError('Unable to Encrypt Passwords.')
    if args.trust and args.mfa:
        raise NotImplementedError('Unable to Use Trusted and MFA Mode.')
    if args.trust and os.path.exists(LPASS_CONFIG_FILE):
        if not args.force:
            raise Exception('Unable to Overwrite Configuration.')
    (_, password) = __get_login(args.username, os.getenv('LPASS_PASSWORD', None), args.mfa)
    if args.trust:
        __write_config(args.username, password, args.mfa)
    __print_message('Logged into {}'.format(__colored(args.username, S_YELLOW)))


def command_logout(args):
    """lpass logout Commandlet"""
    if args.force:
        raise NotImplementedError('Unable to support --force')
    if not os.path.exists(LPASS_CONFIG_FILE):
        raise Exception('Unable to Get Configuration.')
    if not os.path.exists(LPASS_BLOB_FILE):
        raise Exception('Unable to Get Blob.')
    os.remove(LPASS_CONFIG_FILE)
    os.remove(LPASS_BLOB_FILE)
    if os.path.exists(LPASS_CONFIG_FILE):
        raise Exception('Unable to Remove {}. Please get rid of it yourself.'.format(LPASS_CONFIG_FILE))
    if os.path.exists(LPASS_BLOB_FILE):
        raise Exception('Unable to Remove {}. Please get rid of it yourself.'.format(LPASS_BLOB_FILE))
    __print_message(format(__colored('Logged out', S_YELLOW)))


def command_ls(args):
    """lpass ls Commandlet"""
    if args.sync != 'auto':
        raise NotImplementedError('Unable to support Sync Mechanism: {}', args.sync)
    if args.m:
        raise NotImplementedError('Unable to support -m')
    if args.u:
        raise NotImplementedError('Unable to support -u')
    if args.long:
        raise NotImplementedError('Unable to support --long')
    (username, password, mfa) = __read_config()
    (vault, password) = __get_login(username, password, mfa)
    group_accounts = {}
    for account in vault.accounts:
        display = True
        group = account.group.decode()
        if args.group and group != args.group:
            display = False
        if not display:
            continue
        group_accounts_list = group_accounts.get(group, [])
        if account.name:
            group_accounts_list.append(account)
        group_accounts[group] = group_accounts_list
    for group in sorted(group_accounts):
        __print_message(__colored('{}'.format(group or '[Unknown Group]'), S_BLUE))
        group_accounts_list = group_accounts[group]
        for account in group_accounts_list:
            __print_message(__colored('     {} [id: {}]'.format(account.name.decode(), account.id.decode()), S_GREEN))


def command_show(args):
    """lpass show Commandlet"""
    if args.clip:
        raise NotImplementedError('Unable to support --clip')
    if args.attach:
        raise NotImplementedError('Unable to support --attach')
    if args.json:
        raise NotImplementedError('Unable to support --json')
    if args.quiet:
        raise NotImplementedError('Unable to support --quiet')
    if args.long:
        raise NotImplementedError('Unable to support --long')
    if args.basic_regexp:
        raise NotImplementedError('Unable to support --basic-regexp')
    if args.fixed_strings:
        raise NotImplementedError('Unable to support --fixed-strings')

    (username, password, mfa) = __read_config()
    (vault, password) = __get_login(username, password, mfa)

    args.all = args.all or not (args.id or args.name or args.username or args.password or args.url or args.password)

    for account in vault.accounts:
        display = True
        if args.unique != account.id.decode():
            display = False
        if not display:
            continue
        if args.id:
            __print_message(account.id.decode())
        elif args.name:
            __print_message(account.name.decode())
        elif args.username:
            __print_message(account.username.decode())
        elif args.password:
            __print_message(account.password.decode())
        elif args.url:
            __print_message(account.url.decode())
        elif args.notes:
            __print_message(account.notes_string())
        elif args.field:
            try:
                __print_message(attrgetter(args.field)(account).decode())
            except AttributeError:
                try:
                    __print_message(attrgetter(args.field)(account.notes).decode())
                except AttributeError:
                    __print_error('Attribute: {} not found'.format(args.field))
        elif args.all:
            __print_message(
                '{} {}'.format(__colored('{}/{}'.format(account.group.decode(), account.name.decode()), S_BLUE),
                               __colored('[id: {}]'.format(account.id.decode()), S_GREEN)))
            if account.username:
                __print_message('{}: {}'.format(__colored('Username', S_YELLOW), account.username.decode()))
            if account.password:
                __print_message('{}: {}'.format(__colored('Password', S_YELLOW), account.password.decode()))
            if account.url:
                __print_message('{}: {}'.format(__colored('URL', S_YELLOW), account.url.decode()))
            if account.notes:
                __print_message('{}: {}'.format(__colored('Notes', S_YELLOW), account.notes_string()))
            all_fields = account.fields()
            for field in ['group', 'id', 'name', 'username', 'password', 'url', 'notes']:
                all_fields.remove(field)
            for field in all_fields:
                try:
                    __print_message(
                        '{}: {}'.format(__colored(field, S_YELLOW), attrgetter(args.field)(account).decode()))
                except AttributeError:
                    __print_error('Attribute: {} not found'.format(args.field))


def main():
    """Main Program."""
    parser = argparse.ArgumentParser(description='Lastpass CLI in Python.')
    parser.add_argument('--color', type=str, choices=['auto', 'never', 'always'], default='auto')
    subparsers = parser.add_subparsers()

    parser_login = subparsers.add_parser('login', help='Login to Lasspass.')
    parser_login.add_argument('--trust', default=False, action='store_true')
    parser_login.add_argument('--plaintext-key', default=True, action='store_true')
    parser_login.add_argument('--mfa', default=False, action='store_true')
    parser_login.add_argument('--force', '-f', default=False, action='store_true')
    parser_login.add_argument('username', type=str, default=os.getenv('LPASS_USER', None))
    parser_login.set_defaults(func=command_login)

    parser_logout = subparsers.add_parser('logout', help='Logout from Lasspass.')
    parser_logout.add_argument('--force', '-f', type=bool, default=False)
    parser_logout.add_argument('--color', type=str, choices=['auto', 'never', 'always'], default='auto')
    parser_logout.set_defaults(func=command_logout)

    parser_ls = subparsers.add_parser('ls', help='List Lasspass Passwords.')
    parser_ls.add_argument('--sync', type=str, choices=['auto', 'now', 'no'], default='auto')
    parser_ls.add_argument('--long', '-l', default=False, action='store_true')
    parser_ls.add_argument('-m', default=False, action='store_true')
    parser_ls.add_argument('-u', default=False, action='store_true')
    parser_ls.add_argument('group', type=str, nargs='?', default=None, help='Within a Group')
    parser_ls.set_defaults(func=command_ls)

    parser_show = subparsers.add_parser('show', help='Show Lasspass Password.')
    parser_show.add_argument('--sync', type=str, choices=['auto', 'now', 'no'], default='auto')
    parser_show.add_argument('--long', '-l', default=False, action='store_true')
    parser_show.add_argument('--clip', '-c', default=False, action='store_true')
    parser_show.add_argument('--quiet', '-q', default=False, action='store_true')
    parser_show.add_argument('--json', '-j', default=False, action='store_true')
    parser_show.add_argument('--all', default=False, action='store_true')
    parser_show.add_argument('--username', default=False, action='store_true')
    parser_show.add_argument('--name', default=False, action='store_true')
    parser_show.add_argument('--password', default=False, action='store_true')
    parser_show.add_argument('--url', default=False, action='store_true')
    parser_show.add_argument('--notes', default=False, action='store_true')
    parser_show.add_argument('--id', default=False, action='store_true')
    parser_show.add_argument('--field', type=str, default=None)
    parser_show.add_argument('--attach', default=False, action='store_true')
    parser_show.add_argument('--basic-regexp', '-G', default=False, action='store_true')
    parser_show.add_argument('--fixed-strings', '-F', default=False, action='store_true')
    parser_show.add_argument('unique', type=str, default=None, help='Unique Name/Id')
    parser_show.set_defaults(func=command_show)

    args = parser.parse_args()
    global OUTPUT_COLOR
    OUTPUT_COLOR = args.color
    try:
        func = args.func
    except AttributeError:
        func = None
        __print_error(parser.format_help())
    try:
        if func:
            func(args)
    except Exception as exc:
        error_msg = str(exc) or 'Exception Occured'
        __print_error(error_msg)


if __name__ == '__main__':
    main()
