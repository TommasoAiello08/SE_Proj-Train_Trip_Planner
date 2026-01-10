from datetime import datetime
import requests
from urllib.parse import quote
from zoneinfo import ZoneInfo

'''
	API Trenitalia
	Version: 0.1.0
	Visual Laser 10 New - 10/2023
'''

class apitr:
	__decodeJson = True
	def __init__(self, decodeJson:bool = True):
		# decodeJson: True = return dict, False = return text/plain
		self.__decodeJson = decodeJson

	__uris = {
		'InfoMob': 'http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/infomobilitaTicker/',
		'partenze': 'http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/partenze/',
		'arrivi': 'http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/arrivi/',
		'andamento': 'http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/andamentoTreno/',
		'indicazioniViaggio': 'http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/soluzioniViaggioNew/',
		'searchStazione': 'http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/cercaStazione/',
		'StazioniByRegione': 'http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/elencoStazioni/'
	}

	__datetimeFormat = {
		'andamento':'timestamp',
		'indicazioniViaggio':'%Y-%m-%dT%H:%M:%S' 	#YYYY-MM-DDTHH:MM:SS (endpoint may not be available)
	}

	def __format_viaggiatreno_station_datetime(self, date: datetime) -> str:
		"""Format datetime for ViaggiaTreno station endpoints (partenze/arrivi).

		These endpoints expect a *URL-encoded* string like:
		"Sat Jan 10 2026 09:00:00 GMT+0100 (Ora standard dell’Europa centrale)"
		or (summer time):
		"... GMT+0200 (Ora legale dell’Europa centrale)"
		"""
		rome = ZoneInfo('Europe/Rome')
		local_dt = date
		try:
			# If naive, assume Europe/Rome
			if local_dt.tzinfo is None:
				local_dt = local_dt.replace(tzinfo=rome)
			else:
				local_dt = local_dt.astimezone(rome)
		except Exception:
			# Fallback: treat as naive
			pass

		# Determine CET/CEST offset and Italian label
		offset = local_dt.utcoffset() or None
		# Default CET
		gmt = 'GMT+0100'
		label = 'Ora standard dell’Europa centrale'
		if offset is not None and int(offset.total_seconds()) == 7200:
			gmt = 'GMT+0200'
			label = 'Ora legale dell’Europa centrale'

		raw = local_dt.strftime('%a %b %d %Y %H:%M:%S') + f' {gmt} ({label})'
		# Critical: the string must be URL-encoded because it contains spaces and unicode apostrophe
		return quote(raw)

	def __dateTime2Str(self,date: datetime, format:str):
		if (format == 'timestamp'):
			return str(int(date.timestamp()))+'000'
		else:
			return date.strftime(format)
	
	def __request(self, uri):
		x = requests.get(
			uri,
			headers={
				'Accept': 'application/json, text/plain, */*',
				'Accept-Charset': 'utf-8',
				'User-Agent': 'se-proj-train-trip-planner/1.0 (+https://localhost)'
			},
			timeout=12,
		)
		#set to use utf-8
		if (x.status_code == 200):
			try:
				if (self.__decodeJson):
					return x.json()
				else:
					return x.text
			except:
				return x.text
		else:
			return None

	def __minimizeCodStazione(self, codStazione:str):
		codStazione = codStazione[1:]
		return str(int(codStazione))


	####### PUBLIC METHODS #######
	def getInfoMob(self):
		# GET /resteasy/viaggiatreno/infomobilitaTicker/
		return self.__request(self.__uris['InfoMob'])

	def getPartenze(self, idStazione:str, dataora: datetime):
		# GET /resteasy/viaggiatreno/partenze/{codiceStazione}/{orario}
		return self.__request(self.__uris['partenze'] + idStazione 
							+ '/' + self.__format_viaggiatreno_station_datetime(dataora))

	def getArrivi(self, idStazione:str, dataora: datetime):
		# GET /resteasy/viaggiatreno/arrivi/{codiceStazione}/{orario}
		return self.__request(self.__uris['arrivi'] + idStazione 
							+ '/' + self.__format_viaggiatreno_station_datetime(dataora))

	def getAndamento(self, idStazioneOrigine:str, idTreno:str, dataoraPartenza: datetime):
		# GET /resteasy/viaggiatreno/andamentoTreno/{codOrigine}/{numeroTreno}/{dataPartenza}
		return self.__request(self.__uris['andamento'] + idStazioneOrigine + '/' + idTreno 
								+ '/' + self.__dateTime2Str(dataoraPartenza, self.__datetimeFormat['andamento']))

	def getIndicazioniViaggio(self, idStazioneOrigine: str, idStazioneArrivo:str, dataora: datetime):
		# GET /resteasy/viaggiatreno/soluzioniViaggioNew/{codLocOrig}/{codLocDest}/{date}
		idStazioneArrivo = self.__minimizeCodStazione(idStazioneArrivo)
		idStazioneOrigine = self.__minimizeCodStazione(idStazioneOrigine)

		return self.__request(self.__uris['indicazioniViaggio'] + idStazioneOrigine + '/' + idStazioneArrivo
								+ '/' + self.__dateTime2Str(dataora, self.__datetimeFormat['indicazioniViaggio']))

	def searchStazione(self, nomeStazione:str):
		# GET /resteasy/viaggiatreno/cercaStazione/{text}
		return self.__request(self.__uris['searchStazione'] + nomeStazione)

	def getStazioniByRegione(self, codRegione:str):
		# GET /resteasy/viaggiatreno/elencoStazioni/{regione}
		return self.__request(self.__uris['StazioniByRegione'] + codRegione)

	def getCodStazione(self, nomeStazione:str):
		# return codStazione from nomeStazione
		stazioni = self.searchStazione(nomeStazione)
		if (stazioni != None):
			try:
				return [stazione['id'] for stazione in stazioni if stazione['nomeLungo'].lower() == nomeStazione.lower()][0]
			except:
				return None
		else:
			return None
		
	####### TOOLS METHODS #######
	def timestamp2datetime(self, timestamp):
		# convert timestamp with || without millisec to datetime
		try:
			return datetime.fromtimestamp(int(timestamp))
		except:
			return datetime.fromtimestamp(int(timestamp)/1000)
