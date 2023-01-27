# clear down

rm -rf /home/hbarnard/mema/static/media/*/*
sqlite3 /home/hbarnard/mema/db/memories.db 'delete from memories'
