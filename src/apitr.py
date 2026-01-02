from datetime import datetime
import requests

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
		'partenze':'%a %b %d %Y %H:%M:%S GMT+0200 (Ora legale dell’Europa centrale)',
		'arrivi':'%a %b %d %Y %H:%M:%S GMT+0200 (Ora legale dell’Europa centrale)',
		'andamento':'timestamp',
		'indicazioniViaggio':'%Y-%m-%dT%H:%M:%S'	#YYYY-MM-DDTHH:MM:SS
	}

	def __dateTime2Str(self,date: datetime, format:str):
		if (format == 'timestamp'):
			return str(int(date.timestamp()))+'000'
		else:
			return date.strftime(format)
	
	def __request(self, uri):
		x = requests.get(uri, headers={'Accept-Charset': 'utf-8'})
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
								+ '/' + self.__dateTime2Str(dataora, self.__datetimeFormat['partenze']))

	def getArrivi(self, idStazione:str, dataora: datetime):
		# GET /resteasy/viaggiatreno/arrivi/{codiceStazione}/{orario}
		return self.__request(self.__uris['arrivi'] + idStazione 
								+ '/' + self.__dateTime2Str(dataora, self.__datetimeFormat['arrivi']))

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
