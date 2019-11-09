Regularflow
========================================================

This module allows you to create trafic light clusters that interact together to regulate circulation.
Trafic lights are smart and can take decision according to the environnement.

I use Deep-renforcement learning for the first POC and Actor-Critic A2C for the next POC

You need to have Apache Kafka and Zookeper for the stream communication.

# First you need to create topic's partitions : 
## One for Manager's communications and one for traffic lights communications

* Download apache kafka here https://kafka.apache.org/downloads
* Install regularflow with setup :

    ```./setup install```

* Start a kafka's broker and a Zookeper's server
* Run this code in an python's interpreter

```from confluent_kafka.admin import AdminClient, NewTopic

adminConfig = {
                'bootstrap.servers': 'localhost:9092'
              }

topicList = ["manager0", "cluster0", "display"]    # Topic Names
partitions = [4, 4, 4]   # Here replace the number 4 by the number of Trafic light that you want in the cluster
replications = [1, 1, 1]

if __name__ == '__main__' :
    newTopics = []
    adminClient = AdminClient(adminConfig)
    adminClient.delete_topics(topicList)
    adminClient.delete_topics(["__consumer_offsets"])
    for i in range(len(topicList)):
        newTopics.append(NewTopic(topicList[i], partitions[i] , replications[i]))
    print(newTopics)
    adminClient.create_topics(newTopics)

```

# Here it's an example of configuration trafic's light of type "follower"

```
from regularflow import newAgent, startDemo, startAgent

consumerConfig = {
                'bootstrap.servers': 'localhost:9092',
                'group.id': 'cluster0',
                'auto.offset.reset': 'earliest'
                }
producerConfig = {
                'bootstrap.servers': 'localhost:9092'
                 }

agent = newAgent(1, consumerConfig, producerConfig, "cluster0", "manager0","display", "follower")  
agent._setAgents([0]) # Here type the id of the other trafic light in the cluster for the communication
startDemo(agent) # run the agent with startDemo for the non-training mode and with startAgent for the training mode
```
# Here it's an example of configuration trafic's light of type "influencer"

```
from regularflow import newAgent, startDemo, startAgent

consumerConfig = {
                'bootstrap.servers': 'localhost:9092',
                'group.id': 'cluster',
                'auto.offset.reset': 'earliest'
                }
producerConfig = {
                'bootstrap.servers': 'localhost:9092'
                 }


agent = newAgent(0, consumerConfig, producerConfig,"cluster0", "manager0", "display", "influencer")
agent._setAgents([1]) # set the id of other traffic lights in the cluster for communication
agent._setForbidenAgents([1]) # set the follower's id of this influencer
agent._restore("/home/roloman/projet-perso/regularflow/example/saves/save_influencer0") # setup the path of the the saved model
startDemo(agent)  # start agent with startDemo for start with non-training mode
agent._save() # specify the save for save this traffic light
```


# Usage example :

## for an example go in the example directory and run in two different terminal : 
* influencer.py and follower.py
* then run manager0 and manager1


