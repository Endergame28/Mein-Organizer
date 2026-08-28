[app]

android.sdk = 35
android.ndk = 28c

title = Mein Organizer
package.name = meinorganizer
package.domain = org.meinorganizer


source.dir = .
source.include_exts = py,png,jpg,jpeg,json,kv,atlas,wav,m4a

version = 1.0.0

icon.filename = %(source.dir)s/icon.png

requirements = python3,kivy,pyjnius

orientation = portrait
fullscreen = 0

android.api = 35
android.minapi = 23
android.archs = arm64-v8a

android.permissions = READ_MEDIA_IMAGES,READ_MEDIA_VIDEO,READ_MEDIA_AUDIO,RECORD_AUDIO

android.allow_backup = True
android.copy_libs = 1


[buildozer]

log_level = 2
warn_on_root = 1
