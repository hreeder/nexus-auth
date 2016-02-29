from flask.ext.principal import Permission, RoleNeed

ACTIVE_ROLES = [
	'view-timers',
	'create-timer',
	'edit-timer',

	'view-temp-ops',
	'create-temp-op',
	'expire-temp-op',

	'view-user-profile',
	'view-unobscured-vcode',
	'view-own-corp-members',
	'view-any-corp-members',

	'view-supers',

	'view-recon',
	'create-pos',
	'create-goo'
]

view_timers = Permission(RoleNeed('view-timers'))
create_timer = Permission(RoleNeed('create-timer'))
edit_timer = Permission(RoleNeed('edit-timer'))

view_temp_ops = Permission(RoleNeed('view-temp-ops'))
create_temp_op = Permission(RoleNeed('create-temp-op'))
expire_temp_op = Permission(RoleNeed('expire-temp-op'))

view_user_profile = Permission(RoleNeed('view-user-profile'))
view_unobscured_vcode = Permission(RoleNeed('view-unobscured-vcode'))
view_own_corp_members = Permission(RoleNeed('view-own-corp-members'))
view_any_corp_members = Permission(RoleNeed('view-any-corp-members'))

view_supers = Permission(RoleNeed('view-supers'))

view_recon = Permission(RoleNeed('view-recon'))
create_pos = Permission(RoleNeed('create-pos'))
create_goo = Permission(RoleNeed('create-goo'))
