# vinted_client.py
import aiohttp
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VintedClient:
    def __init__(self, search_url: str):
        if not search_url:
            raise ValueError("L'URL de recherche Vinted ne peut pas être vide.")
        self.search_url = search_url
        self.seen_item_ids = set()
        self.first_run = True

    async def search_new_items(self) -> list:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                api_search_url = f"https://www.vinted.fr/api/v2/catalog/items?{self.search_url.split('?')[-1]}"
                async with session.get(api_search_url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    items = data.get("items", [])
                    
                    if not items:
                        logging.warning("Aucun article trouvé. Vérifiez les filtres de votre URL de recherche.")
                        return []

                    new_items = []
                    current_item_ids = {item['id'] for item in items}

                    if self.first_run:
                        self.seen_item_ids = current_item_ids
                        self.first_run = False
                        logging.info(f"Initialisation Vinted : {len(self.seen_item_ids)} articles actuels mémorisés.")
                    else:
                        new_item_ids = current_item_ids - self.seen_item_ids
                        if new_item_ids:
                            new_items = [item for item in items if item['id'] in new_item_ids]
                            logging.info(f"Détection Vinted : {len(new_items)} nouveaux articles trouvés !")
                        self.seen_item_ids.update(new_item_ids)
                    return new_items
            except aiohttp.ClientError as e:
                logging.error(f"Erreur API Vinted : {e}")
                return []
            except Exception as e:
                logging.error(f"Erreur inattendue dans VintedClient : {e}")
                return []
