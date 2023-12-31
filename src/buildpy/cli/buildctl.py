import click
import attr, attrs

import buildpy.proc
import buildpy.provider
import buildpy.util
from buildpy.config import Config
from buildpy.context import AppContext

attr.s, attr.ib = attrs.define, attrs.field


@click.group(context_settings=dict(auto_envvar_prefix='BUILDCTL'))
@click.pass_context
def buildctl(cctx: click.Context):
	cctx.obj = ctx = AppContext(
		config=Config(),
	)
	cctx.with_resource(ctx)
	buildpy.provider.setup(ctx)


@buildctl.command(name='review-repo')
@click.pass_obj
def review_repo(ctx: AppContext):
	config = ctx.config

	# find pkgbuilds
	pkgbuilds = buildpy.proc.find_pkgbuilds(config)
	# load pkgbuilds -> [pkgbase, [pkgname]]
	buildpy.proc.load_pkgbuilds(pkgbuilds, config)
