const { MongoClient } = require('mongodb');

async function removeDuplicatesFromServerNames() {
  const uri = 'YOUR_MONGO_URI_HERE';
  const client = new MongoClient(uri);

  try {
    await client.connect();
    const db = client.db('YOUR_DB_NAME');
    const users = db.collection('users');

    const cursor = users.find({ server_names: { $exists: true, $type: 'array' } });

    while (await cursor.hasNext()) {
      const doc = await cursor.next();
      const original = doc.server_names;
      const deduped = [...new Set(original)];

      if (original.length !== deduped.length) {
        await users.updateOne(
          { _id: doc._id },
          { $set: { server_names: deduped } }
        );
        console.log(`Fixed user ${doc.user_id}`);
      }
    }
  } finally {
    await client.close();
  }
}

removeDuplicatesFromServerNames();