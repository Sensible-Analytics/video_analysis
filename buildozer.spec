[app]
title = Video Analysis
package.name = video_analysis
package.domain = org.sensible_analytics
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt,vtt
version = 0.1
requirements = python3,requests,python-dotenv,slugify,ffmpeg-python,numpy
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
android.api = 31
android.minapi = 21
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.ios_deploy_url = https://github.com/ios-control/ios-deploy
ios.ios_deploy_branch = master
