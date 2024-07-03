from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
import config

app = Flask(__name__)
app.secret_key = 'your_secret_key'

client = MongoClient(config.MONGO_URI)
db = client[config.DB_WAREHOUSE]
collection = db[config.COLLECTION_PRODUCT]
collectionkeluar = db[config.COLLECTION_PRODUCT_KELUAR]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/input_produk.html', methods=['GET', 'POST'])
def input_produk():
    if request.method == 'POST':
        id_produk = request.form['id_produk']
        nama_produk = request.form['nama_produk']
        kode_produk = request.form['kode_produk']
        stok = int(request.form['stok'])
        harga = float(request.form['harga'])
        tanggal_masuk = request.form['tanggal_masuk']
        
        # Cek apakah id_produk sudah ada di collection
        if collection.find_one({'ID_Produk': id_produk}):
            session['message'] = 'ID Produk sudah ada, harap gunakan ID yang berbeda!'
            return redirect(url_for('input_produk'))
        
        collection.insert_one({
            'ID_Produk': id_produk,
            'Nama_Produk': nama_produk,
            'Kode_Produk': kode_produk,
            'Stok': stok,
            'Harga_Produk': harga,
            'Tanggal_masuk': tanggal_masuk
        })
        
        session['message'] = 'Produk berhasil diinput!'
        return redirect(url_for('input_produk'))
    
    produk_list = collection.find()
    message = session.pop('message', None)
    
    return render_template('input_produk.html', produk_list=produk_list, message=message)

#update input_produk
@app.route('/update_produk/<id_produk>', methods=['POST'])
def update_produk(id_produk):
    if request.method == 'POST':
        data = request.json
        nama_produk = data['Nama_Produk']
        kode_produk = data['Kode_Produk']
        stok = int(data['Stok'])
        harga = float(data['Harga_Produk'])
        tanggal_masuk = data['Tanggal_masuk']

        # Lakukan update ke MongoDB
        result = collection.update_one(
            {'ID_Produk': id_produk},
            {
                '$set': {
                    'Nama_Produk': nama_produk,
                    'Kode_Produk': kode_produk,
                    'Stok': stok,
                    'Harga_Produk': harga,
                    'Tanggal_masuk': tanggal_masuk
                }
            }
        )

        if result.modified_count > 0:
            session['message'] = 'Produk berhasil diupdate!'
        else:
            session['message'] = 'Gagal melakukan update'

        return jsonify({'message': session['message']})
    
    #delete input_produk
@app.route('/delete_produk/<id_produk>', methods=['POST'])
def delete_produk(id_produk):
    result = collection.delete_one({'ID_Produk': id_produk})
    
    if result.deleted_count > 0:
        session['message'] = 'Produk berhasil di hapus!'
    else:
        session['message'] = 'Gagal menghapus produk'
        
    return redirect(url_for('input_produk'))
        
       
#produk keluar
@app.route('/produk_keluar.html', methods=['GET', 'POST'])
def produk_keluar():
    if request.method == 'POST':
        id_produk_keluar = request.form['id_produk_keluar']
        nama_produk = request.form['nama_produk']
        stok_keluar = int(request.form['stok'])
        cabang_toko = request.form['cabang_toko']
        tanggal_keluar = request.form['tanggal_keluar']
        
        # Cari produk berdasarkan Nama_Produk
        produk = collection.find_one({'Nama_Produk': nama_produk})
        
        if produk:
            id_produk = produk['ID_Produk']
            harga = produk['Harga_Produk']
            tanggal_masuk = produk['Tanggal_masuk']
            
            if collectionkeluar.find_one({'ID_Produk_Keluar': id_produk_keluar}):
                session['message'] = 'ID Produk Keluar sudah ada, harap gunakan ID yang berbeda!'
                return redirect(url_for('produk_keluar'))
            
            # Simpan data produk keluar ke dalam collectionkeluar
        if stok_keluar <= produk['Stok']:
        
            collectionkeluar.insert_one({
                'ID_Produk_Keluar': id_produk_keluar,
                'ID_Produk': id_produk,
                'Nama_Produk': nama_produk,
                'Stok': stok_keluar,
                'Harga': harga,
                'Cabang_Toko': cabang_toko,
                'Tanggal_Masuk': tanggal_masuk,
                'Tanggal_Keluar': tanggal_keluar
            })
            
            new_stock = produk['Stok'] - stok_keluar
            collection.update_one(
                {'ID_Produk': id_produk },
                {'$set' : {'Stok' : new_stock}}
            )
            
            session['message'] = 'Produk keluar berhasil!'
            return redirect(url_for('produk_keluar'))
        else:
            session['message'] = 'Stok tidak mencukupi untuk produk ini'
            return redirect(url_for('produk_keluar'))
    
    # Ambil daftar produk dari collection
    produk_list = collection.find()
    produk_keluar_list = collectionkeluar.find()
    message = session.pop('message', None)
    
    return render_template('produk_keluar.html', produk_list=produk_list, produk_keluar_list=produk_keluar_list, message=message)


@app.route('/delete_produk_keluar/<id_produk_keluar>', methods=['DELETE'])
def delete_produk_keluar(id_produk_keluar):
    result = collectionkeluar.delete_one({'ID_Produk_Keluar': id_produk_keluar})
    
    if result.deleted_count > 0:
        session['message'] = 'Data produk keluar berhasil dihapus!'
        return jsonify({'success': True}), 200
    else:
        session['message'] = 'Gagal menghapus data produk keluar'
        return jsonify({'success': False}), 404


@app.route('/laporan.html')
def laporan():
    
    produk_masuk_list = list(collection.find())
    
    produk_keluar_list = list(collectionkeluar.find())
    
    return render_template('laporan.html', produk_masuk_list=produk_masuk_list, produk_keluar_list=produk_keluar_list)
    
   
if __name__ == '__main__':
    app.run(debug=True, port=8080)
