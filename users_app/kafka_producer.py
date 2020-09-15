from aiokafka import AIOKafkaProducer


async def send_one(app, topic, data):
    config = app['config']
    producer = AIOKafkaProducer(
        loop=app.loop, bootstrap_servers=config['bootstrap_servers'])

    await producer.start()
    try:
        await producer.send(
            topic,
            data.encode('utf-8')
        )
    finally:
        await producer.stop()
