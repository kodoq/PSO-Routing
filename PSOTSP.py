import numpy as np
import json
from urllib.request import urlopen
# from urllib import urlopen
import random
import math
import time


start_time = time.time()
global places, hstart, mstart, dstart, allDestinasi
hstart = 8 # jam berangkat
mstart = 0 # menit berangkat
dstart = 5 # hari berangkat
jumIndividu = 100 #Populasi Partikel 
epoch = 100 
coef1 = 0.5
coef2 = 0.5
coef3 = 0.5

allDestinasi = []
with open('data.csv', 'r') as f:
    for a in f.readlines():
        data = a.split(',')
        jadwal = []
        for tanggal in range(1,8):
            if (data[tanggal] != '-') and (data[tanggal+7] != '-'):
                jadwal.append([data[tanggal].replace(':','').rjust(4,'0'),data[tanggal+7].replace(':','').rjust(4,'0')])
            else:
                jadwal.append(['-','-'])
        allDestinasi.append([data[0],jadwal,data[15].strip().replace(':','').rjust(4,'0')])



#epoch atau konvergensi

global API_KEY
API_KEY = 'AIzaSyAyWHO5GcJnbteW-662nXeqwGPGU_mZriA'
# AIzaSyDVSnxhH1PohWRUP6c1H3GX0ITioSZRphQ API key lain
# AIzaSyAyWHO5GcJnbteW-662nXeqwGPGU_mZriA
class API:
	def distance(self, origin, destination):
		url = 'https://maps.googleapis.com/maps/api/distancematrix/json?origins='+str.replace(origin,' ','+')+'&destinations='+str.replace(destination,' ','+')+'&key='+API_KEY
		request = urlopen(url)
		return json.load(request)

class Places:
	def __init__(self,list_perjalanan,open_close,transit_time):
		self.list_perjalanan = np.array(list_perjalanan)
		self.open_close = np.array(open_close)
		for i in range(len(transit_time)):
			jam = int(transit_time[i][:2]) * 3600
			menit = int(transit_time[i][2:]) * 60
			transit_time[i] = jam + menit
		self.transit_time = np.array(transit_time)
		self.api = API()
		print ('Requesting travel time...')
		self.set_lamaPerjalanan()

	def set_lamaPerjalanan(self):
		self.jarakwaktu = np.zeros([self.list_perjalanan.shape[0],self.list_perjalanan.shape[0]])
		for i in range(self.list_perjalanan.shape[0]):
			for j in range(self.list_perjalanan.shape[0]):
				if i != j:
					print ("Request travel time",self.list_perjalanan[i],"->",self.list_perjalanan[j])
					hasil = self.api.distance(self.list_perjalanan[i],self.list_perjalanan[j])
					self.jarakwaktu[i,j] = hasil['rows'][0]['elements'][0]['duration']['value']


class Particle:
	def __init__(self, position, velocity):
		self.position = position
		self.velocity = velocity
		self.personalBest = self
		self.setFitness()
    
	def setPersonalBest(self, newParticle):
		self.personalBest = newParticle
    
	def setFitness(self):
		arrTime = np.arange(0,24)
		arrDay = np.arange(0,7) #pertama iki yod, ki nggo circular day 0-6
		dcurrent = dstart
		self.lamaperjalanan = 0.0
		self.daylist = []
		self.waktu_tempuh = []
		while True:
			if(places.open_close[self.position[0]][dcurrent][0] != "-"): break
			dcurrent += 1
			dcurrent = dcurrent % (arrDay.shape[0] + 1)
			self.lamaperjalanan += 24 #skip 1 hari = lama perjalanan ditambah 24 jam
			self.daylist.append([])
			self.waktu_tempuh.append(0)
		#openclose[index destinasi][index hari][0 buka, 1 tutup][2 digit pertama jam, 2 digit terahir menit]
		jambuka = int(places.open_close[self.position[0]][dcurrent][0][:2])
		jamtutup = int(places.open_close[self.position[0]][dcurrent][1][:2])
		bukaRange = []
		#start nambah jam2 buka ke array bukaRange
		startIndex = np.where(arrTime == jambuka)[0] + 1
		while True:
			if(arrTime[startIndex % arrTime.shape[0]] == jamtutup): break
			bukaRange.append(arrTime[startIndex % arrTime.shape[0]])
			startIndex += 1
		#end
		if not(hstart in bukaRange):
			startIndex = np.where(arrTime == hstart)[0] + 1
			jarakwaktu = 0
			while True:
				if(arrTime[startIndex % arrTime.shape[0]] == jambuka): break
				startIndex += 1
				jarakwaktu += 1
				if (startIndex > arrTime.shape[0]):
					dcurrent += 1
					dcurrent = dcurrent % (arrDay.shape[0] + 1)
			self.lamaperjalanan += jarakwaktu
			hcurrent = int(places.open_close[self.position[0]][dcurrent][0][:2])
			mcurrent = (int(places.open_close[self.position[0]][dcurrent][0][2:]))
		else:
			hcurrent, mcurrent = hstart, mstart
		timeconvert = (places.jarakwaktu[0,self.position[0]] + places.transit_time[self.position[0]]) / 3600.0
		timeconvert2 = (places.jarakwaktu[0,self.position[0]]) / 3600.0
		currentday = [self.position[0]]
		self.lamaperjalanan += timeconvert
		self.fitness = 0
		hsampai, msampai = self.getwaktu(timeconvert2, hcurrent, mcurrent)
		hcurrent, mcurrent = self.getwaktu(timeconvert, hcurrent, mcurrent)
		self.jamtiapjalan = [str(hcurrent)+":"+str(mcurrent)]
		self.jamsampai = [str(hsampai)+":"+str(msampai)]
		for i in range(len(self.position) - 1):
			timeconvert = ((places.jarakwaktu[self.position[i],self.position[i+1]]) + places.transit_time[self.position[i+1]]) / 3600.0
			timeconvert2 = (places.jarakwaktu[self.position[i],self.position[i+1]]) / 3600.0
			# kondisi tutup
			while True:
				if(places.open_close[self.position[i + 1]][dcurrent][0] != "-"): break
				dcurrent += 1
				dcurrent = dcurrent % (arrDay.shape[0] + 1)
				self.lamaperjalanan += 24 #skip 1 hari = lama perjalanan ditambah 24 jam
				self.daylist.append(currentday)
				if (len(currentday) > 0): self.waktu_tempuh.append(self.lamaperjalanan - sum(self.waktu_tempuh))
				else: self.waktu_tempuh.append(0)
				currentday = []
				hcurrent, mcurrent = hstart, mstart

			if self.cekTempatTutup(hcurrent, mcurrent, places.open_close[self.position[i + 1]][dcurrent], timeconvert):
				if (len(currentday) != 0):
					self.daylist.append(currentday)
					self.waktu_tempuh.append(self.lamaperjalanan - sum(self.waktu_tempuh))
				currentday = [self.position[i+1]]
				# hitung waktu pulang
				timeconvert = (places.jarakwaktu[self.position[i],0]) / 3600.0
				self.lamaperjalanan += timeconvert
				# hitung waktu jarak mulai perjalanan awal, dari jam awal dengan detik
				jambuka,jamtutup = int(places.open_close[self.position[i + 1]][dcurrent][0][:2]),int(places.open_close[self.position[i + 1]][dcurrent][1][:2])
				bukaRange = []
				startIndex = np.where(arrTime == jambuka)[0] + 1
				while True:
					if(arrTime[startIndex % arrTime.shape[0]] == jamtutup): break
					bukaRange.append(arrTime[startIndex % arrTime.shape[0]])
					startIndex += 1
				if not(hstart in bukaRange):
					startIndex = np.where(arrTime == hstart)[0] + 1
					jarakwaktu = 0
					while True:
						if(arrTime[startIndex % arrTime.shape[0]] == jambuka): break
						startIndex += 1
						jarakwaktu += 1
						if (startIndex > arrTime.shape[0]):
							dcurrent += 1
							dcurrent = dcurrent % (arrDay.shape[0] + 1)
					self.lamaperjalanan += jarakwaktu
					hcurrent = int(places.open_close[self.position[i + 1]][dcurrent][0][:2])
					mcurrent = (int(places.open_close[self.position[i + 1]][dcurrent][0][2:]))
				else:
					hcurrent, mcurrent = hstart, mstart
				# hitung waktu berangkat lagi
				timeconvert = ((places.jarakwaktu[0,self.position[i+1]]) + places.transit_time[self.position[i+1]]) / 3600.0
				timeconvert2 = (places.jarakwaktu[0,self.position[i+1]]) / 3600.0
				self.lamaperjalanan += timeconvert
			else:
				# kondisi buka
				currentday.append(self.position[i+1])
				self.lamaperjalanan += timeconvert
			hsampai, msampai = self.getwaktu(timeconvert2, hcurrent, mcurrent)
			hcurrent, mcurrent = self.getwaktu(timeconvert, hcurrent, mcurrent)
			self.jamtiapjalan.append(str(hcurrent)+":"+str(mcurrent))
			self.jamsampai.append(str(hsampai)+":"+str(msampai))
		self.daylist.append(currentday)
		self.lamaperjalanan += places.jarakwaktu[self.position[-1],0] / 3600.0 #waktu tempuh
		self.waktu_tempuh.append(self.lamaperjalanan - sum(self.waktu_tempuh))
		self.fitness = self.fitness + (1 / self.lamaperjalanan) #kualitas antibody
    
	def getwaktu(self, timeconvert, hcurrent, mcurrent):
		hresult = hcurrent + int(timeconvert)
		mresult = mcurrent + int(round((timeconvert - int(timeconvert))*60))
		menit = mresult%60
		hresult += (mresult-menit)/60
		hresult = hresult%24
		mresult = menit 
		return hresult,mresult

	def cekTempatTutup(self, hcurrent, mcurrent, open_close, lamajalanstay):
		arrTime = np.arange(0,24)
		hend = hcurrent + int(lamajalanstay)
		mend = mcurrent + int(round((lamajalanstay - int(lamajalanstay))*60))
		menit = mend%60
		hend += (mend-menit)/60
		hend = hend%24
		mend = menit

		jambuka,jamtutup = int(open_close[0][:2]),int(open_close[1][:2])
		menitbuka, menitutup = int(open_close[0][2:]),int(open_close[1][2:])
		bukaRange = []
		startIndex = np.where(arrTime == jambuka)[0] + 1
		while True:
			if(arrTime[startIndex % arrTime.shape[0]] == jamtutup): break
			bukaRange.append(arrTime[startIndex % arrTime.shape[0]])
			startIndex += 1
		return not(((hcurrent in bukaRange) or ((hcurrent == jambuka) and (mcurrent > menitbuka))) and ((hend in bukaRange) or ((hend == jamtutup) and (mend < menitutup))))

class DPSO:
    def __init__(self, c1, c2, c3,populasi,jumDestinasi, epoch):
        self.c1 = c1
        self.c2 = c2
        self.c3 = c3
        self.globalBest = None
        self.particle = []
        for i in range(1,populasi):
            destinasi = list(range(1,jumDestinasi))
            random.shuffle(destinasi)
            self.particle.append(Particle(destinasi,[random.sample(range(1,jumDestinasi),2)]))
            
        self.setGlobalBest()
        self.running(epoch)

    def operasiC(self,const,velocity):
        c = abs(const)
        if c == 0 :
            return []
        elif c >0 and c <=1 :
            velocityBaru = int(math.ceil(len(velocity)* c))
            return velocity[:velocityBaru]	
        else :
            k = int(c)
            cAksen = int(math.ceil(len(velocity)* (k-c)))
            return velocity * k + velocity[:cAksen] 

    def operasiPosisi(self,p1,p2):
        hasil = []
        for partikel in range(len(p1)):
            if p1[partikel] != p2[partikel] and not([p2[partikel],p1[partikel]] in hasil):
                hasil.append([p1[partikel],p2[partikel]])
        return hasil

    def setGlobalBest(self):
        self.particle.sort(key=lambda x: x.fitness, reverse=True)
        if self.globalBest == None or self.globalBest.fitness < self.particle[0].fitness:
            self.globalBest = self.particle[0]

    def positionFinding(self):
        newColony = []
        for oneparticle in self.particle:
            operasiC1 = self.operasiC(self.c1,oneparticle.velocity)
            operasiC2 = self.operasiC(self.c2, self.operasiPosisi(oneparticle.personalBest.position[:], oneparticle.position[:]))
            operasiC3 = self.operasiC(self.c3,self.operasiPosisi(self.globalBest.position[:],oneparticle.position[:]))
            hasil = operasiC1 + operasiC2 + operasiC3
            newPosition = oneparticle.position[:]
            for v in hasil:
                tempA, tempB = newPosition.index(v[0]), newPosition.index(v[1])
                newPosition[tempA], newPosition[tempB] = newPosition[tempB], newPosition[tempA]
            newParticle = Particle(newPosition, hasil)

            if newParticle.fitness < oneparticle.personalBest.fitness:
                newParticle.setPersonalBest(oneparticle.personalBest)

            newColony.append(newParticle)
        
        self.particle = newColony


    
    def running(self, epoch):
        for i in range(epoch):
            self.positionFinding()
            self.setGlobalBest()
            print(i+1, self.globalBest.lamaperjalanan, self.globalBest.position)


list_perjalanan = [
  'Hotel Horison Bandung',
  allDestinasi[91][0],
  allDestinasi[42][0], #pilih destinasi ng iki, allDestinasi[index tempat][0 = nama, 1 = open_close, 2 = lama stay]
  allDestinasi[2][0],
  allDestinasi[3][0],
  allDestinasi[29][0],
#   allDestinasi[32][0],
#   allDestinasi[5][0]
 ]
open_close = [
  [' '], 
  allDestinasi[91][1],
  allDestinasi[42][1],
  allDestinasi[2][1],
  allDestinasi[3][1],
  allDestinasi[29][1],
#   allDestinasi[32][1],
#   allDestinasi[5][1]
 ]
transit_time = [
  '0300',
  allDestinasi[91][2],
  allDestinasi[42][2],
  allDestinasi[2][2],
  allDestinasi[3][2],
  allDestinasi[29][2],
#   allDestinasi[32][2],
#   allDestinasi[5][2]
 ]
# list_perjalanan = []
# open_close = [[' ']]
# transit_time = ['0000']
# list_perjalanan.append(input('Masukkan nama hotel awal: '))
# answer = 'y'
# destinasi = 1
# while answer.lower() == 'y':
# 	print ('Masukkan nama destinasi ke-%i: ' % destinasi)
# 	list_perjalanan.append(input())
# 	buka = input('Jam buka[hhmm]: ')
# 	tutup = input('Jam tutup[hhmm]: ')
# 	open_close.append([buka, tutup])
# 	transit_time.append(input('transit_time[hhmm]: '))
# 	answer = input('Masukkan destinasi selanjutnya?(y/n) ')
	# destinasi += 1
listhari = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
places = Places(list_perjalanan,open_close,transit_time)
print ("[Antigen]\n==========================================")
print ("Berikut adalah time matrix antar tempat wisata: ")
print (" ")
print (places.jarakwaktu,"\n\n")
dpso = DPSO(coef1, coef2, coef3, jumIndividu, len(list_perjalanan),epoch)
jam = int(dpso.globalBest.lamaperjalanan)
menit = round((dpso.globalBest.lamaperjalanan - jam) * 60)
print ("Total Waktu Perjalanan:",jam,"Jam",menit,"Menit")
print ("List perjalanan tiap hari: ")
print ("Berangkat dari: ", list_perjalanan[0])
k = 0
for i in range(len(dpso.globalBest.daylist)):
	print ("Hari "+listhari[dstart + i])
	print ("Destinasi :")
	for j in range(len(dpso.globalBest.daylist[i])):
		print ("\t"+str(j+1)+". "+list_perjalanan[dpso.globalBest.daylist[i][j]]+". Pukul: "+dpso.globalBest.jamsampai[k]+" s.d "+dpso.globalBest.jamtiapjalan[k])
		k += 1
	jam = int(dpso.globalBest.waktu_tempuh[i])
	menit = round((dpso.globalBest.waktu_tempuh[i] - jam) * 60)
	print ("\tWaktu Perjalanan:",jam,"Jam",menit,"Menit")

print("--- %s seconds ---" % (time.time() - start_time))


# coba = Particle([1,2,3,4],[])
# jam = int(coba.lamaperjalanan)
# menit = round((coba.lamaperjalanan - jam) * 60)
# print ("Total Waktu1 Perjalanan:",jam,"Jam",menit,"Menit")
# print ("List perjalanan tiap hari1: ")
# print ("Berangkat dari: ", list_perjalanan[0])
# k = 0
# for i in range(len(coba.daylist)):
# 	print ("Hari ke-"+str(i+1))
# 	print ("Destinasi :")
# 	for j in range(len(coba.daylist[i])):
# 		print ("\t"+str(j+1)+". "+list_perjalanan[coba.daylist[i][j]]+". Pukul: "+coba.jamsampai[k]+" s.d "+coba.jamtiapjalan[k])
# 		k += 1
# 	jam = int(coba.waktu_tempuh[i])
# 	menit = round((coba.waktu_tempuh[i] - jam) * 60)
# 	print ("\tWaktu Perjalanan:",jam,"Jam",menit,"Menit")


# coba2 = Particle([2,1,3,4],[])
# jam = int(coba2.lamaperjalanan)
# menit = round((coba2.lamaperjalanan - jam) * 60)
# print ("Total Waktu1 Perjalanan:",jam,"Jam",menit,"Menit")
# print ("List perjalanan tiap hari2: ")
# print ("Berangkat dari: ", list_perjalanan[0])
# k = 0
# for i in range(len(coba2.daylist)):
# 	print ("Hari ke-"+str(i+1))
# 	print ("Destinasi :")
# 	for j in range(len(coba2.daylist[i])):
# 		print ("\t"+str(j+1)+". "+list_perjalanan[coba2.daylist[i][j]]+". Pukul: "+coba2.jamsampai[k]+" s.d "+coba2.jamtiapjalan[k])
# 		k += 1
# 	jam = int(coba2.waktu_tempuh[i])
# 	menit = round((coba2.waktu_tempuh[i] - jam) * 60)
# 	print ("\tWaktu Perjalanan:",jam,"Jam",menit,"Menit")


# coba2 = Particle([4,3,2,1],[])
# jam = int(coba2.lamaperjalanan)
# menit = round((coba2.lamaperjalanan - jam) * 60)
# print ("Total Waktu1 Perjalanan:",jam,"Jam",menit,"Menit")
# print ("List perjalanan tiap hari2: ")
# print ("Berangkat dari: ", list_perjalanan[0])
# k = 0
# for i in range(len(coba2.daylist)):
# 	print ("Hari ke-"+str(i+1))
# 	print ("Destinasi :")
# 	for j in range(len(coba2.daylist[i])):
# 		print ("\t"+str(j+1)+". "+list_perjalanan[coba2.daylist[i][j]]+". Pukul: "+coba2.jamsampai[k]+" s.d "+coba2.jamtiapjalan[k])
# 		k += 1
# 	jam = int(coba2.waktu_tempuh[i])
# 	menit = round((coba2.waktu_tempuh[i] - jam) * 60)
# 	print ("\tWaktu Perjalanan:",jam,"Jam",menit,"Menit")
