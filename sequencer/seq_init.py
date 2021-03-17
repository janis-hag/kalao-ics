#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

async def init_FLI_cam():
	#await ...
	pass

async def check_PLC_init_status():
	#await ...
	pass

async def init_CACAO():
	#await ...
	pass

async def init_system():

	await asyncio.gather(
		init_FLI_cam(),
		check_PLC_init_status(),
		init_CACAO()
	)


asyncio.run(init_system())
