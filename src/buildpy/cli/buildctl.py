import click
import attr, attrs

import buildpy.proc
import buildpy.util
from buildpy.config import Config

attr.s, attr.ib = attrs.define, attrs.field


@attr.s
class AppContext:
	config: Config


@click.group(context_settings=dict(auto_envvar_prefix='BUILDCTL'))
@click.pass_context
def buildctl(ctx: click.Context):
	ctx.obj = AppContext(
		config=Config(),
	)
	pass


@buildctl.command(name='review-repo')
@click.pass_obj
def review_repo(ctx: AppContext):
	config = ctx.config

	# find pkgbuilds
	pkgbuilds = buildpy.proc.find_pkgbuilds(config)
	# load pkgbuilds -> [pkgbase, [pkgname]]
	buildpy.proc.load_pkgbuilds(pkgbuilds, config)
