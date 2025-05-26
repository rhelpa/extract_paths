1) Extract playlists csv from PLEX
2) Run parse_playlists.py on all-playlists.csv (renamed from PLEX download) -- outputs separate playlist-name.csv files
3) Run build_map.py <playlist-name.csv> -- outputs media-map-playlist-Name.txt
4) Bash push_map.sh on media-map-playlist-Name.txt from FS42 console