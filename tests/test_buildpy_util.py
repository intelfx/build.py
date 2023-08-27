import subprocess
from pathlib import Path

import pytest
import attr, attrs
attr.s, attr.ib = attrs.define, attrs.field

import buildpy.util
import tests.util
from tests.util import tmp_file


CUSTOM_NAME = 'custom'
CUSTOM_SECTION = r'''
Server = https://domain.tld/repo
'''.strip('\n')

PACMAN_CONF = r'''
#
# /etc/pacman.conf
#
# See the pacman.conf(5) manpage for option and repository directives

#
# GENERAL OPTIONS
#
[options]
# The following paths are commented out with their default values listed.
# If you wish to use different paths, uncomment and update the paths.
#RootDir     = /
#DBPath      = /var/lib/pacman/
#CacheDir    = /var/cache/pacman/pkg/
#LogFile     = /var/log/pacman.log
#GPGDir      = /etc/pacman.d/gnupg/
#HookDir     = /etc/pacman.d/hooks/
HoldPkg     = pacman glibc
#XferCommand = /usr/bin/curl -L -C - -f -o %o %u
#XferCommand = /usr/bin/wget --passive-ftp -c -O %o %u
#CleanMethod = KeepInstalled
Architecture = auto

# Pacman won't upgrade packages listed in IgnorePkg and members of IgnoreGroup
#IgnorePkg   =
#IgnoreGroup =

#NoUpgrade   =
#NoExtract   =

# Misc options
#UseSyslog
#Color
NoProgressBar
# We cannot check disk space from within a chroot environment
#CheckSpace
VerbosePkgLists
ParallelDownloads = 5

# By default, pacman accepts packages signed by keys that its local keyring
# trusts (see pacman-key and its man page), as well as unsigned packages.
SigLevel    = Required DatabaseOptional
LocalFileSigLevel = Optional
#RemoteFileSigLevel = Required

# NOTE: You must run `pacman-key --init` before first using pacman; the local
# keyring can then be populated with the keys of all official Arch Linux
# packagers with `pacman-key --populate archlinux`.

#
# REPOSITORIES
#   - can be defined here or included from another file
#   - pacman will search repositories in the order defined here
#   - local/custom mirrors can be added here or in separate files
#   - repositories listed first will take precedence when packages
#     have identical names, regardless of version number
#   - URLs will have $repo replaced by the name of the current repo
#   - URLs will have $arch replaced by the name of the architecture
#
# Repository entries are of the format:
#       [repo-name]
#       Server = ServerName
#       Include = IncludePath
#
# The header [repo-name] is crucial - it must be present and
# uncommented to enable the repo.
#

# The testing repositories are disabled by default. To enable, uncomment the
# repo name header and Include lines. You can add preferred servers immediately
# after the header, and they will be used before the default mirrors.

#[core-testing]
#Include = /etc/pacman.d/mirrorlist

[core]
Include = /etc/pacman.d/mirrorlist

#[extra-testing]
#Include = /etc/pacman.d/mirrorlist

[extra]
Include = /etc/pacman.d/mirrorlist

# An example of a custom package repository.  See the pacman manpage for
# tips on creating your own repositories.
#[custom]
#SigLevel = Optional TrustAll
#Server = file:///home/custompkgs
'''.strip('\n')
PACMAN_CONF_CUSTOM_PREPEND = r'''
#
# /etc/pacman.conf
#
# See the pacman.conf(5) manpage for option and repository directives

#
# GENERAL OPTIONS
#
[options]
# The following paths are commented out with their default values listed.
# If you wish to use different paths, uncomment and update the paths.
#RootDir     = /
#DBPath      = /var/lib/pacman/
#CacheDir    = /var/cache/pacman/pkg/
#LogFile     = /var/log/pacman.log
#GPGDir      = /etc/pacman.d/gnupg/
#HookDir     = /etc/pacman.d/hooks/
HoldPkg     = pacman glibc
#XferCommand = /usr/bin/curl -L -C - -f -o %o %u
#XferCommand = /usr/bin/wget --passive-ftp -c -O %o %u
#CleanMethod = KeepInstalled
Architecture = auto

# Pacman won't upgrade packages listed in IgnorePkg and members of IgnoreGroup
#IgnorePkg   =
#IgnoreGroup =

#NoUpgrade   =
#NoExtract   =

# Misc options
#UseSyslog
#Color
NoProgressBar
# We cannot check disk space from within a chroot environment
#CheckSpace
VerbosePkgLists
ParallelDownloads = 5

# By default, pacman accepts packages signed by keys that its local keyring
# trusts (see pacman-key and its man page), as well as unsigned packages.
SigLevel    = Required DatabaseOptional
LocalFileSigLevel = Optional
#RemoteFileSigLevel = Required

# NOTE: You must run `pacman-key --init` before first using pacman; the local
# keyring can then be populated with the keys of all official Arch Linux
# packagers with `pacman-key --populate archlinux`.

#
# REPOSITORIES
#   - can be defined here or included from another file
#   - pacman will search repositories in the order defined here
#   - local/custom mirrors can be added here or in separate files
#   - repositories listed first will take precedence when packages
#     have identical names, regardless of version number
#   - URLs will have $repo replaced by the name of the current repo
#   - URLs will have $arch replaced by the name of the architecture
#
# Repository entries are of the format:
#       [repo-name]
#       Server = ServerName
#       Include = IncludePath
#
# The header [repo-name] is crucial - it must be present and
# uncommented to enable the repo.
#

# The testing repositories are disabled by default. To enable, uncomment the
# repo name header and Include lines. You can add preferred servers immediately
# after the header, and they will be used before the default mirrors.

[custom]
Server = https://domain.tld/repo

#[core-testing]
#Include = /etc/pacman.d/mirrorlist

[core]
Include = /etc/pacman.d/mirrorlist

#[extra-testing]
#Include = /etc/pacman.d/mirrorlist

[extra]
Include = /etc/pacman.d/mirrorlist

# An example of a custom package repository.  See the pacman manpage for
# tips on creating your own repositories.
#[custom]
#SigLevel = Optional TrustAll
#Server = file:///home/custompkgs
'''.strip('\n')


def test_pacman_conf(tmp_file):
	pacman_conf = tmp_file(PACMAN_CONF, prefix="pacman", suffix=".conf")
	with buildpy.util.pacman_conf_prepend_repo(pacman_conf, CUSTOM_NAME, CUSTOM_SECTION) as output_conf:
		assert output_conf.read() == PACMAN_CONF_CUSTOM_PREPEND


@pytest.mark.xfail
def test_pacman_conf2(tmp_file):
	pacman_conf = tmp_file(PACMAN_CONF, prefix="pacman", suffix=".conf")
	with buildpy.util.pacman_conf_prepend_repo2(pacman_conf, CUSTOM_NAME, CUSTOM_SECTION) as output_conf:
		assert output_conf.read() == PACMAN_CONF_CUSTOM_PREPEND


@attr.s
class PopenFiles:
	nr: int
	basedir: Path
	names: list[str]
	names_with_bad: list[str]
	paths: list[Path]
	paths_with_bad: list[Path]


@pytest.fixture
def popen_files(tmp_path):
	# enough to fill a pipe buffer
	NR_FILES = 1000
	filenames = [ f'file{i}' for i in range(NR_FILES) ]
	filepaths = [ tmp_path/n for n in filenames ]
	for p in filepaths:
		p.touch()
	badname = 'file_does_not_exist'
	badpath = tmp_path/badname

	return PopenFiles(
		nr=NR_FILES,
		basedir=tmp_path,
		names=filenames,
		names_with_bad=filenames + [badname],
		paths=filepaths,
		paths_with_bad=filepaths + [badpath],
	)


def test_popen_success(popen_files):
	with buildpy.util.Popen(
			['ls', '-1', popen_files.basedir],
			text=True,
			stdin=subprocess.DEVNULL,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
	) as f:
		stdout = tests.util.readlines_list(f.stdout)
		assert set(stdout) == set(popen_files.names)
		stderr = tests.util.readlines_list(f.stderr)
		assert not stderr


def test_popen_nonzero(popen_files):
	with buildpy.util.Popen(
			['ls', '-1'] + popen_files.paths_with_bad,
			text=True,
			stdin=subprocess.DEVNULL,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
	) as f:
		stdout = tests.util.readlines_list(f.stdout)
		assert set(stdout) == set(map(str, popen_files.paths))
		stderr = tests.util.readlines_list(f.stderr)
		assert len(stderr) == 1
		assert f.wait() != 0


def test_popen_success_check(popen_files):
	with buildpy.util.Popen(
			['ls', '-1', popen_files.basedir],
			text=True,
			check=True,
			stdin=subprocess.DEVNULL,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
	) as f:
		stdout = tests.util.readlines_list(f.stdout)
		assert set(stdout) == set(popen_files.names)
		stderr = tests.util.readlines_list(f.stderr)
		assert not stderr


def test_popen_nonzero_check(popen_files):
	with pytest.raises(subprocess.CalledProcessError):
		with buildpy.util.Popen(
				['ls', '-1'] + popen_files.paths_with_bad,
				text=True,
				check=True,
				stdin=subprocess.DEVNULL,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
		) as f:
			stdout = tests.util.readlines_list(f.stdout)
			assert set(stdout) == set(map(str, popen_files.paths))
			stderr = tests.util.readlines_list(f.stderr)
			assert len(stderr) == 1


def test_popen_nonzero_check_raises(popen_files):
	with pytest.raises(subprocess.CalledProcessError) as exc_info:
		with buildpy.util.Popen(
				['ls', '-1'] + popen_files.paths_with_bad,
				text=True,
				check=True,
				stdin=subprocess.DEVNULL,
				stdout=subprocess.PIPE,
				stderr=subprocess.STDOUT,
		) as f:
			filepaths_str = set(map(str, popen_files.paths))
			# must raise eventually
			for line in tests.util.readlines(f.stdout):
				if line not in filepaths_str:
					raise RuntimeError(f'got an unexpected line: {line}')

	assert type(exc_info.value) is subprocess.CalledProcessError
	assert type(exc_info.value.__context__) is RuntimeError
