"""
@author: Dionisius Salvavictori Wanggur
@NPM: 2017730005
"""
# import Library
import time
import threading
import multiprocessing
from pusher import pusher
from datetime import datetime
from mysql.connector import pooling
from mysql.connector import Error
import hashlib
from digi.xbee.devices import XBeeDevice
from digi.xbee.devices import RemoteXBeeDevice


# Global Variable
statusSensor = 0 # 0 mati, 1 hidup

# thread running
threadRunning = False

# status aplikasi
isApprun = True

# thread array
arrayOfThread = []

# simpan node yang aktif
activeNode ={}

# pusher, merupakan API untuk melakukan komunikasi
# secara real-time melalui web socket
pusher_client = pusher.Pusher(
    app_id ='1388664',
    key = 'a189c31a94dae4644a9f',
    secret='1059d367deb12f596d60',
    cluster='ap1',
    ssl = True
)


# inisiasi Xbee menggunakan library digiXbee
device = XBeeDevice("/dev/ttyUSB0",9600)
device.open()

# database mysql properties
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name = 'ptnative_pool',
        pool_size = 5,
        pool_reset_session = True,
        host = 'sql6.freesqldatabase.com',
        user = 'sql6497913',
        password = 'SzMHWg7yye',
        buffered = True,
        database = 'sql6497913'
    )
    # bikin 2 connection baru, 1 untuk thread sensing data, 1 untuk operasi sekali pakai
    mydb = connection_pool.get_connection()
    mydb2 = connection_pool.get_connection()  
except:
    print("error connect to database")
        

# menu untuk tampilan program
def menu():
    print("------------------------------------------------------------")
    print("*** Selamat Datang Pada Aplikasi Pemantauan Hidroponik ***")
    print()
    print("Status Node Sensor Saat Ini:")
    checkStatus()
    print("###############################")
    print()
    print("Menu Program")
    print("---------------------------")
    print()
    print("1. Start Proses Sensing")
    print("2. Stop Proses Sensing")
    print("3. Daftar Akun pengguna")
    print("4. Update Password Pengguna")
    print("5. Tutup Program")
    print()
    print("---------------------------")
    print()   
    

# method utama untuk menjalankan aplikasi pada base station
def main():
    global isApprun
    global statusSensor
    global arrayOfThread
    
    # Tampilan Awal Aplikasi Pemantauan Hidroponik Admin
    menu()
    
    while isApprun == True:
        global threadRunning
        UsermenuInput = input("Masukan Nomor Program >>>  ")

        if UsermenuInput == "1":
            print("...... Sensing Started ......")
            nodesStatus = checkStatus()
            
            if len(nodesStatus)!= 0:
                print("Status Sensor Saat Ini: ")
                nodeSensor = getNodeSensor()
                counter = 1
                for item in nodeSensor:
                    # menampilkan semua node sensor
                    status = int(item["Status"])
                    if status == 0:
                        print(str(counter) + ". " + item["namaNode"] + " Status: Mati")
                    else:
                        print(str(counter) + ". " + item["namaNode"] + " Status: Sedang Melakukan Sensing")

                    counter+=1
                print()
                
                # set status sensor
                statusSensor = 1
                
                # inisiasi thread untuk menjalankan proses sensing di background
                t1 = threading.Thread(target = startSensing, args=(nodesStatus,))
                t1.daemon = True
                
                # jalankan thread
                t1.start()
                arrayOfThread.append(t1)
                # set thread running
                threadRunning = True
            else:
                print("Status Sensor Saat Ini:" )
                checkStatus()
            
        elif UsermenuInput == "2":
            # set status sensor
            statusSensor  = 0
            
            # memberhentikan thread
            if threadRunning == True:
                for item in arrayOfThread:
                    item.join()
                threadRunning = False
            
            # cek status node
            print("Status Sensor Saat Ini:" )
            nodes = checkStatus()
            
            if len(nodes) !=0:
                # method untuk memberhentikan proses sensing
                stopSensing(nodes)
            
        elif UsermenuInput == "3":
            # menu untuk menambahkan pengguna baru
            print("Daftar Pengguna Baru")
            print("Silahkan Masukan Nama Pengguna Baru !!!")
            nama = input()
            
            print("Silahkan Masukan Username Pengguna Baru !!!")
            username = input()
            
            print("Silahkan Masukan Email Pengguna Baru !!!")
            email = input()
            
            print("Silahkan Masukan Password Pengguna Baru !!!")
            password = input()
            
            # Menambahkan User ke Database
            insertUser(nama,username,email,password)

        elif UsermenuInput == "4":
            print("Update Password Pengguna")
            print("Silahkan Pilih Pengguna !!!")
            
            # Ambil semua data pengguna yang ada di database
            pengguna = getPengguna()
            
            # Nomor Menu
            counter = 1
            
            # array untuk menyimpan idpengguna
            idPengguna = []
            
            for item in pengguna:
                # menampilkan semua pengguna
                print(str(counter) + ". " + item["nama"])
                counter+=1
                
                # simpan semua idpengguna ke dalam array
                idPengguna.append(item["idPengguna"])

            penggunaTerpilih = input("Masukan Nomor Pengguna >>> ")

            print("Silahkan Masukan password Baru !!!")
            password = input()
            
            # update password pengguna
            updatePassPengguna(idPengguna[int(penggunaTerpilih)-1], password)
        
        elif UsermenuInput == "999":
            UsermenuInput = input("Masukan Hidden Program >>>  ")

            if UsermenuInput == "5":
                print("Hidden Menu 5: Menambahkan Node Sensor Baru")
                print("Silahkan Pilih Sistem Hidroponik Terlebih Dahulu !!!")
                
                # ambil semua data sistem hidroponik yang terdaftar pada database.
                sistemHidroponik = getSistemHidroponik()
                
                # Nomor Menu
                counter = 1
                
                # array untuk menyimpan idHidroponik
                idHidroponik = []
                for item in sistemHidroponik:
                    # menampilkan semua sistem hidroponik
                    print(str(counter) + ". " + item["namaHidroponik"] + " Lokasi : " + item["lokasi"])
                    counter+=1
                    
                     #simpan semua idhidroponik ke dalam array
                    idHidroponik.append(item["idHidroponik"])

                sistemHidroponikTerpilih = input("Masukan Nomor Sistem Hidroponik >>> ")

                print("Silahkan Masukan Nama Node Sensor Baru !!!")
                namaNodeSensor = input()
                
                # menambahkan node sensor kedalam database
                tambahNodeSensor(idHidroponik[int(sistemHidroponikTerpilih)-1], namaNodeSensor)
                
            elif UsermenuInput == "6":
                print("Hidden Menu 6: Menambahkan Sistem Hidroponik Baru")
                namaSistemHidroponik = input("Masukan Nama Sistem Hidroponik Baru! >>> ")
                lokasi = input("Masukan Lokasi Penempatan Sensor di Sistem Hidroponik! >>> ")
                # menambahkan Sistem hidroponik baru
                tambahSistemHidroponik(namaSistemHidroponik, lokasi)
                
            elif UsermenuInput == "7":
                print("Hidden Menu 7: Menambahkan Sensor Baru Pada Node Sensor")
                print("Silahkan Pilih Node Sensor Terlebih Dahulu !!!")
                
                # ambil semua data node sensor yang terdaftar pada database.
                nodeSensor = getNodeSensor()
                
                # Nomor Menu
                counter = 1
                
                # array untuk menyimpan idHidroponik
                idNode = []
                for item in nodeSensor:
                    # menampilkan semua node sensor
                    print(str(counter) + ". " + item["namaNode"])
                    counter+=1
                    
                    #simpan semua id node sensor ke dalam array
                    idNode.append(item["idNode"])

                nodeSensorTerpilih = input("Masukan Nomor Node Sensor >>> ")
                namaSensor = input("Silahkan Masukan Nama Sensor Baru !!! >>> ")
                batasAtas = input("Masukan Nilai Peringatan Batas Atas >>> ")
                batasBawah= input("Masukan Nilai Peringatan Batas Bawah >>> ")
                
                # menambahkan sensor kedalam database
                tambahSensor(idNode[int(nodeSensorTerpilih)-1], namaSensor,float(batasAtas),float
                (batasBawah))
            else:
                print("Menu Tidak Ditemukan")
        elif UsermenuInput == "5":
            if mydb.is_connected():
                cursor = mydb.cursor()
                cursor.close()
                mydb.close()
            quit()
        else:
            print("!!! Masukan Salah !!!")
            print()
            menu()
            

# method ini digunakan untuk memeriksa status dari node sensor
def checkStatus():
    global activeNode
    activeNode = {}
    # mencari node yang aktif
    xnet = device.get_network()
    xnet.clear()
    xnet.start_discovery_process(deep=True, n_deep_scans=1)
    while xnet.is_discovery_running():
        time.sleep(0.5)
    
    nodes = xnet.get_devices()
    if len(nodes)!=0:
        for item in nodes:
            remote = RemoteXBeeDevice(device, item.get_64bit_addr())
            
            try:
                #  send data
                device.send_data(remote, "check")
                # incoming berisi data, timeout 20 detik
                incoming = device.read_data_from(remote,20)
                
                if incoming !=None:
                    # decode data 
                    incoming = incoming.data.decode("utf8")
                    # format pesan dipisahkan dengan '|'
                    incoming = incoming.split("|")
                    # ambil nama node
                    namaNode = incoming[0]
                    # incoming ke 1 akan berisi status dari node sensor, 1=mati, 0=Hidup;
                    statusSensor  = int(incoming[1])
                    
                    # setiap kali data diterima set status sensor
                    setStatusNodeSensor(int(incoming[1]),namaNode)
                    print(namaNode + " Sedang Aktif.")
                    activeNode[item.get_64bit_addr()] = namaNode
                
            except:
                print(" Peringatan: Node Sensor Bermasalah !!!")
    else:
        print("...Tidak Ada Node yang Aktif....")
        print("Hidupkan Perangkat Node Sensor Terlebih Dahulu")
    print()
    return nodes

# method ini digunakan untuk menambahkan sebuah node sensor baru
# pada jaringan WSN (Wireless Sensor Network)
def tambahNodeSensor(idHidroponik,namaNodeSensor):
    cursor = mydb2.cursor()

    query = "INSERT INTO nodeSensor (idHidroponik,namaNode,status) VALUES(%s,%s,%s)"
    value = (idHidroponik,namaNodeSensor,0)

    cursor.execute(query,value,multi=True)
    mydb.commit()
    
# method ini digunakan untuk mengubah password pengguna
def updatePassPengguna(idPengguna,password):
    # encode String password
    password_enc = password.encode()
    
    #call hash function
    d = hashlib.sha256(password_enc)
    
    #generate binary hash
    hash_pass = d.hexdigest()
    
    cursor = mydb2.cursor()

    query = "UPDATE pengguna SET password = %s WHERE idPengguna = %s"
    value = (hash_pass,idPengguna)

    cursor.execute(query,value)
    mydb2.commit()
    print("Password Berhasil Diubah")


# method ini digunakan untuk menambahkan sebuah node sensor baru
# pada jaringan WSN (Wireless Sensor Network)
def tambahSensor(idNode,namaSensor, batasAtas, batasBawah):
    cursor = mydb2.cursor()

    query = "INSERT INTO sensor (idNode,namaSensor,batasAtas, batasBawah) VALUES(%s,%s,%s,%s)"
    value = (idNode,namaSensor,batasAtas, batasBawah)

    cursor.execute(query,value,multi=True)
    mydb.commit()

# method ini digunakan untuk menampilkan sistem hidroponik
# yang telah terdaftar di database
def getSistemHidroponik():
    cursor = mydb2.cursor(dictionary = True)

    query = "SELECT * FROM hidroponik"

    cursor.execute(query,multi=True)
    sistemHidroponik = cursor.fetchall()
    return sistemHidroponik

# method ini digunakan untuk menampilkan seluruh pengguna
# yang telah terdaftar di database
def getPengguna():
    if mydb2.is_connected():
        cursor = mydb2.cursor(dictionary = True)

        query = "SELECT * FROM pengguna"

        cursor.execute(query)
        pengguna = cursor.fetchall()
        return pengguna

# method ini digunakan untuk mendaftarkan pengguna baru
def insertUser(nama, username, email, password):
    # encode String password
    password_enc = password.encode()
    
    #call hash function
    d = hashlib.sha256(password_enc)
    
    #generate binary hash
    hash_pass = d.hexdigest()
    
    cursor = mydb2.cursor()
    query = "INSERT INTO pengguna (nama,username,email,password) VALUES(%s,%s,%s,%s)"
    value = (nama,username,email,hash_pass)

    cursor.execute(query,value)
    mydb2.commit()
    print("Pengguna Berhasil Ditambahkan")

# method ini digunakan untuk menambahkan sebuah Sistem Hidroponik baru
# yang akan dipantau dengan menggunakan jaringan WSN (Wireless Sensor Network)
def tambahSistemHidroponik(namaSistem,lokasi):
    cursor = mydb2.cursor
    query = "INSERT INTO hidroponik (namaHidroponik, lokasi) VALUES(%s,%s)"
    value = (namaSistem,lokasi)

    cursor.execute(query,value,multi=True)
    mydb2.commit()
    
# method ini digunakan untuk menampilkan node sensor
# yang telah terdaftar di database
def getNodeSensor():
    cursor = mydb.cursor(dictionary = True)
    query = "SELECT * FROM nodeSensor"
    cursor.execute(query)
    nodeSensor = cursor.fetchall() 
    return nodeSensor

# method ini digunakan untuk mengembalikan id dari node sensor
# yang telah terdaftar di database
def getNodeSensorID(nama):
    cursor = mydb.cursor()
    query = "SELECT idNode FROM nodeSensor WHERE namaNode = %s"
    value = (nama,)
    cursor.execute(query,value)
    nodeSensor = cursor.fetchall()[0][0]
    return nodeSensor

# method ini digunakan untuk mengubah status dari node sensor
def setStatusNodeSensor(status,namaNode):
    cursor = mydb.cursor()
    query = "UPDATE nodeSensor SET Status = %s WHERE namaNode LIKE %s"
    value = (status,namaNode)
    
    cursor.execute(query,value)
    mydb.commit()
        
# method ini digunakan untuk mengirim perintah untuk menjalankan
# proses sensing yang akan dijalankan oleh node sensor
def startSensing(nodes):
    global activeNode
    global statusSensor
    namaNode =""
    while statusSensor == 1:
        for item in nodes:
            remote = RemoteXBeeDevice(device, item.get_64bit_addr())
            try:
                # perintah start sensing
                device.send_data(remote,"start")
                
                # incoming berisi data, timeout 20 detik
                incoming = device.read_data_from(remote,20)
                
                # jika data tidak kosong
                if incoming != None:
                    # decode data
                    incoming = incoming.data.decode("utf8")
                    
                    # setiap format pesan dipisahkan dengan '|'
                    incoming = incoming.split("|")
                    
                    # ambil namaNode
                    namaNode = incoming[0]
                    
                    # ambil idNode dari database berdasarkan data yang diterima
                    idNode = getNodeSensorID(namaNode)
                    
                    # ambil data suhu udara
                    suhuUdara = float(incoming[2])
                    
                    # ambil data suhu air
                    suhuAir = float(incoming[3])
                    
                    # ambil data pH
                    pH = float(incoming[4])
                    
                    # ambil data kelembaban
                    kelembaban = float(incoming[5])
                    
                    # ambil data TDS
                    TDS = float(incoming[6])
                    
                    # setiap kali data diterima set status sensor
                    setStatusNodeSensor(int(incoming[1]),namaNode)
                    
                    # insert sensing data
                    insertSensingData(idNode,suhuUdara, suhuAir, pH, kelembaban, TDS)
                    
                    # insert data untuk disimpan dalam tabel histori
                    insertSensingDataHistory(idNode,suhuUdara, suhuAir, pH, kelembaban, TDS)
            except:
                print()
                namaNode = activeNode[item.get_64bit_addr()]
                print("****** Warning *******")
                print("Peringatan Node Sensor: "+ namaNode+" Bermasalah")
                
                # jika data tidak diterima dalam waktu 20 detik
                setStatusNodeSensor(0,namaNode)
                
                # kirim notifikasi ke pusher 
                message = {'message': 'success'}
                pusher_client.trigger('my-channel', 'my-event', message)
                print()
                print("Status Sensor Saat Ini:" )
                nodes = checkStatus()
                print()
                print("Hentikan Proses Sensing untuk Sementara Waktu !!! Tekan 2")
                statusSensor=0
    print()

# method ini digunakan untuk mengirim perintah untuk memberhentikan
# proses sensing yang akan dijalankan oleh node sensor
def stopSensing(nodes):
    for item in nodes:
        remote = RemoteXBeeDevice(device, item.get_64bit_addr())
        
        try:
            #  send data
            device.send_data(remote, "stop")
            # incoming berisi data, timeout 20 detik
            incoming = device.read_data_from(remote,20)
            # jika data tidak kosong
            if incoming != None:
                # decode data
                incoming = incoming.data.decode("utf8")
                
                # setiap format pesan dipisahkan dengan '|'
                incoming = incoming.split("|")
                
                # ambil namaNode
                namaNode = incoming[0]
                
                # setiap kali data diterima set status sensor
                setStatusNodeSensor(int(incoming[1]),namaNode)
                # stop proses sensing
                print("Stop Proses Sensing " + namaNode)
                
        except:
            print("Node Sensor Bermasalah")
    print()
    
    # kirim notifikasi ke pusher 
    message = {'message': 'success'}
    pusher_client.trigger('my-channel', 'my-event', message) 
    
# method ini digunakan untuk meng-update value dari sensor pada database
def insertSensingData(idNode, suhuUdara, suhuAir, pH, kelembaban, TDS):
    data = {}
    data["suhuUdara"] = suhuUdara
    data["suhuAir"] = suhuAir
    data["pH"] = pH
    data["kelembaban"] = kelembaban
    data["TDS"] = TDS
    
    waktu = datetime.now()
    cursor = mydb.cursor()
   
    for x in data:
        if x == "suhuUdara":
            query = "UPDATE sensor SET value = %s, waktu = %s WHERE idNode = %s AND namaSensor LIKE 'Suhu Udara'"
            value = (suhuUdara, waktu, idNode)

            cursor.execute(query,value)
            mydb.commit()
        elif x == "suhuAir":
            query = "UPDATE sensor SET value = %s, waktu = %s WHERE idNode = %s AND namaSensor LIKE 'Suhu Air'"
            value = (suhuAir, waktu, idNode)

            cursor.execute(query,value)
            mydb.commit()
        elif x == "pH":
            query = "UPDATE sensor SET value = %s, waktu = %s WHERE idNode = %s AND namaSensor LIKE 'pH'"
            value = (pH, waktu, idNode)

            cursor.execute(query,value)
            mydb.commit()
        elif x == "kelembaban":
            query = "UPDATE sensor SET value = %s, waktu = %s WHERE idNode = %s AND namaSensor LIKE 'Kelembaban'"
            value = (kelembaban, waktu, idNode)

            cursor.execute(query,value)
            mydb.commit()
        elif x == "TDS":
            query = "UPDATE sensor SET value = %s, waktu = %s WHERE idNode = %s AND namaSensor LIKE 'TDS'"
            value = (TDS, waktu, idNode)

            cursor.execute(query,value)
            mydb.commit()
        
    # kirim notifikasi ke pusher 
    message = {'message': 'success'}
    pusher_client.trigger('my-channel', 'my-event', message)

# method ini digunakan untuk mengirim history data sensing ke database
def insertSensingDataHistory(idNode, suhuUdara, suhuAir, pH, kelembaban, TDS):
    cursor = mydb.cursor()
    query = "INSERT INTO sense (idNode, waktu, suhuUdara, suhuAir, pH, kelembaban,TDS) VALUES (%s,%s,%s,%s,%s,%s,%s)"
    value = (idNode,datetime.now(), suhuUdara, suhuAir, pH, kelembaban, TDS)

    cursor.execute(query,value)
    mydb.commit()
    

if __name__ =='__main__':
    main()
