from typing import List, Dict
from torrent.torrent_item import TorrentItem
from debrid.alldebrid import AllDebrid
from debrid.realdebrid import RealDebrid
from debrid.premiumize import Premiumize

from utils.logger import setup_logger

class TorrentSmartContainer:
    def __init__(self, torrent_items: List[TorrentItem]):
        self.logger = setup_logger(__name__)
        self.__itemsDict: Dict[TorrentItem] = self.__build_items_dict_by_infohash(torrent_items)
    
    def get_hashes(self):        
        return self.__itemsDict.keys()
    
    def update_availability(self, debrid_response, debrid_type):
        if debrid_type is RealDebrid:
            self.__update_availability_realdebrid(debrid_response)
        elif debrid_type is AllDebrid:
            self.__update_availability_alldebrid(debrid_response)
        elif debrid_type is Premiumize:
            self.__update_availability_premiumize(debrid_response)
        else:
            raise NotImplemented

    def __update_availability_realdebrid(self, response):
        for info_hash, details in response.items():
            if "rd" not in details:
                continue
        
            torrent_item: TorrentItem = self.__itemsDict[info_hash]

            files = []
            if torrent_item.type == "series":
                season = torrent_item.season.replace("S","")
                episode = torrent_item.episode.replace("E","")
                
                for variants in details["rd"]:
                    for file_index, file in variants.items():
                        if self.__series_season_episode_available(file["filename"], season, episode):
                            files.append({
                                "file_index": file_index,
                                "title": file["filename"],
                                "size": file["filesize"]
                            })
            else:
                for variants in details["rd"]:
                    for file_index, file in variants.items():
                        files.append({
                            "file_index": file_index,
                            "title": file["filename"],
                            "size": file["filesize"]
                        })

            self.__update_file_details(torrent_item, files)

    def __update_availability_alldebrid(self, response):
        if response["status"] != "success":
            return
        
        for data in response["data"]["magnets"]:
            if data["instant"] == False:
                continue
            
            torrent_item: TorrentItem = self.__itemsDict[data["hash"]]
            
            files = []
            if torrent_item.type == "series":
                season = torrent_item.season.replace("S","")
                episode = torrent_item.episode.replace("E","")

                file_index = 1
                for file in data["files"]:
                    if self.__series_season_episode_available(file["n"], season, episode):
                        files.append({
                            "file_index": file_index,
                            "title": file["n"],
                            "size": file["s"]
                        })
                    file_index += 1
            else:
                file_index = 1
                for file in data["files"]:
                    files.append({
                        "file_index": file_index,
                        "title": file["n"],
                        "size": file["s"]
                    })
                    file_index += 1

            self.__update_file_details(torrent_item, files)

    def __update_availability_premiumize(self, response):
        #I don't understand the premiumize api
        pass

    def __update_file_details(self, torrent_item, files):
        if len(files) == 0:
            return
        
        file = max(files, key = lambda file: file["filesize"])
        torrent_item.availability = True
        torrent_item.file_index = file["size"]
        torrent_item.title = file["title"]
        torrent_item.size = file["size"]

    def __build_items_dict_by_infohash(self, items: List[TorrentItem]):
        items_dict = dict()
        for item in items:
            if item.info_hash is not None:
                items_dict[item.info_hash] = item
        return items_dict

    def __series_season_episode_available(self, filename, season, episode):   
        return season in filename and episode in filename and filename.index(season) < filename.index(episode)
