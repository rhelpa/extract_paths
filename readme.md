1) Extract all-playlists.csv from PLEX/Tautulli
2) Run parse_playlists.py to separate playlists into playlist-<station_name>.csv
3) Run build_map.py playlist-<station_name>.csv to create media-map-playlist-<station_name>.txt
4) Upload media-map-playlist-<station_name>.txt to server
5) Run push_map.sh on FS42 server
