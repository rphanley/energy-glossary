import os
import re
import datetime




from dotenv import load_dotenv
from flask import Flask, render_template, redirect, request, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId


load_dotenv(override=True)
app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'energy_glossary'
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'Env value not loaded')

mongo = PyMongo(app)


@app.route('/')
@app.route('/home')
def home():
    latest = mongo.db.terms.find().sort('_id',-1).limit(10)
    return render_template("index.html", records=latest)




@app.route('/search_terms', methods=['POST'])
def search_terms():
    result = None
    
    #Get the search text from the input box
    search_text = request.form['search_input']
    #Run a case-insensitive search for a record with term=search_text
    try:
        result = mongo.db.terms.find_one({'term': re.compile(search_text, re.IGNORECASE)})
       
    except:
        # Notify the user
        msg = 'Error accessing the database! Check your database access and try again.'
        return render_template("message.html",
                                message_text=msg)

    
    # Print an error if no result found, otherwise get the result record.
    if not result:
        msg = 'No result found for: ' + search_text + ' .Check your spelling and try again.'
        return render_template("message.html",
                                message_text=msg)
    else:
        print("Found a database entry for: " + search_text)
        term_id = result['_id']
        return redirect(url_for('get_record', record_id=term_id))


@app.route('/get_record/<record_id>')
def get_record(record_id):
    badge = ''
    print('Getting record ID ' + record_id)
    record = mongo.db.terms.find_one({'_id': ObjectId(record_id)})
    print('Got record ID with term: ' + record['term'])
    if created_today(record_id):
        badge = 'new badge'
    return render_template("read.html",
                                result_term=record, badge_class=badge)


# Check if the database entry was created today, for New badge
def created_today(entry_id):
    obj_id = ObjectId(entry_id)
    create_date = obj_id.generation_time.date()
    print(create_date)
    today = datetime.datetime.utcnow().date()
    print(today)
    return (create_date == today)

@app.route('/add')
def add():
    return render_template('add.html')



@app.route('/update/<term_id>')
def update(term_id):
    term = mongo.db.terms.find_one({"_id": ObjectId(term_id)})
    return render_template('update.html', term_to_update=term)



#Perform the record insertion in the database
@app.route('/add_entry', methods=['POST'])
def add_entry():
    terms =  mongo.db.terms
    # Add a new record
    terms.insert_one({
        'term':request.form.get('term_name'),
        'description':request.form.get('term_description'),
        })
    print('Added record..')
    return redirect(url_for('home'))

#Perform the record update in the database
@app.route('/update_entry/<term_id>', methods=['POST'])
def update_entry(term_id):
    terms =  mongo.db.terms

    #Update the record
    terms.update( {'_id': ObjectId(term_id)},
        {
        'term':request.form.get('term_name'),
        'description':request.form.get('term_description'),
        })
    print('Updated record..')
    return redirect(url_for('home'))


@app.route('/delete/<term_id>')
def delete(term_id):
    entry = mongo.db.terms.find_one({"_id": ObjectId(term_id)})
    name = entry['term']
    mongo.db.terms.delete_one({'_id': ObjectId(term_id)})
    # Notify the user
    msg = 'Entry for ' + '"' + name + '"' + ' deleted!'

    return render_template("message.html",
                                message_text=msg)
         
    


if __name__ == '__main__':
    app.run(host=os.environ.get('IP','0.0.0.0'),
            port=int(os.environ.get('PORT','5000')),
            debug=True)
