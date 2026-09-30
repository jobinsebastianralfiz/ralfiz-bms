# Practice set 4.7: big data systems and NoSQL

Time: 24 minutes (about 90 seconds per problem). No notes. Assume a block size of 128 MB and a replication factor of 3 unless a problem says otherwise.

**1.** A 700 MB file is stored in HDFS. How many blocks, how many block replicas, and how much raw disk space does it use?
(1) 5 blocks, 15 replicas, 1,920 MB  (2) 6 blocks, 18 replicas, 2,304 MB  (3) 6 blocks, 18 replicas, 2,100 MB  (4) 6 blocks, 6 replicas, 700 MB

**2.** A cluster has 12 DataNodes of 16 TB each. What is its usable capacity with replication factor 3, and with replication factor 2?
(1) 64 TB and 96 TB  (2) 192 TB and 192 TB  (3) 48 TB and 64 TB  (4) 64 TB and 128 TB

**3.** A job reads four files of 100 MB, 260 MB, 128 MB and 129 MB. Splits follow block boundaries and files are not combined. How many map tasks run?
(1) 5  (2) 6  (3) 7  (4) 8

**4.** Word count with a sum combiner. Mapper 1 reads the lines "sun moon sun" and "star". Mapper 2 reads "moon moon star sun". How many pairs does the map phase emit in total, how many are shuffled after combining, and what are the final counts?
(1) 8, 6; sun 3, moon 3, star 2  (2) 8, 8; sun 3, moon 3, star 2  (3) 6, 6; sun 2, moon 3, star 2  (4) 8, 3; sun 3, moon 3, star 2

**5.** With 3 reducers and partitioner hash(key) mod 3, the hashes are sun = 11, moon = 7 and star = 6. Which reducer receives each key, and how many output files does the job write?
(1) sun 2, moon 1, star 0; 3 files  (2) sun 1, moon 2, star 0; 3 files  (3) sun 2, moon 1, star 0; 1 file  (4) sun 2, moon 2, star 0; 2 files

**6.** Match List I with List II.

| List I (Daemon) | List II (Job) |
|---|---|
| A. NameNode | I. Stores blocks and sends heartbeats |
| B. DataNode | II. Merges the edit log into the fsimage |
| C. Secondary NameNode | III. Holds the namespace and the block map |
| D. NodeManager | IV. Launches and monitors containers on one node |

(1) A-III, B-I, C-II, D-IV  (2) A-I, B-III, C-II, D-IV  (3) A-III, B-I, C-IV, D-II  (4) A-III, B-II, C-I, D-IV

**7.** Arrange in order: A. Reduce  B. Combine  C. Map  D. Shuffle and sort  E. Input split
(1) E, C, D, B, A  (2) C, E, B, D, A  (3) E, C, B, D, A  (4) E, B, C, D, A

**8.** A store keeps N = 4 replicas. Which (R, W) pair guarantees that every read sees the latest write?
(1) (1, 3)  (2) (2, 2)  (3) (2, 3)  (4) (3, 1)

Problems 9–11 use this collection:

    orders:
    {_id:1, cust:"Ravi", amount:450,  status:"paid",      items:["pen","ink"]}
    {_id:2, cust:"Sara", amount:1200, status:"pending",   items:["paper"]}
    {_id:3, cust:"Ravi", amount:800,  status:"paid",      items:["paper","pen"]}
    {_id:4, cust:"Tom",  amount:300,  status:"cancelled"}
    {_id:5, cust:"Sara", amount:650,  status:"paid",      items:["ink"]}

**9.** What does db.orders.countDocuments({status: "paid", amount: {$gte: 600}}) return?
(1) 1  (2) 2  (3) 3  (4) 4

**10.** What is the output of this aggregation?

    db.orders.aggregate([ {$match: {status: "paid"}},
      {$group: {_id: "$cust", total: {$sum: "$amount"}}},
      {$sort: {total: -1}} ])

(1) Ravi 1250, Sara 650  (2) Sara 1850, Ravi 1250  (3) Ravi 1250, Sara 1850  (4) Sara 650, Ravi 1250

**11.** What does db.orders.countDocuments({items: "pen"}) return?
(1) 0  (2) 1  (3) 2  (4) 3

**12.** What do the two print statements output?

    words = sc.parallelize(["ink pen", "pen paper pen"]).flatMap(lambda s: s.split())
    print(words.count())
    print(words.distinct().count())

(1) 2 and 2  (2) 5 and 5  (3) 3 and 5  (4) 5 and 3

**13.** Assertion (A): A replicated store configured with N = 3, R = 1 and W = 1 may return stale data.
Reason (R): When R + W ≤ N, a read quorum need not overlap the replicas that took the latest write.
(1) Both (A) and (R) are true and (R) is the correct explanation of (A)  (2) Both (A) and (R) are true but (R) is NOT the correct explanation of (A)  (3) (A) is true but (R) is false  (4) (A) is false but (R) is true

**14.** Which of the following are correct?
A. Cassandra is a column-family store.  B. CouchDB is a document store.  C. Neo4j is queried with Cypher.  D. Redis is a graph database.  E. HBase stores its data on HDFS.
(1) A, B and C only  (2) A, B, C and E only  (3) B, C, D and E only  (4) A, C and E only

**15.** Statement I: With consistent hashing, adding a node moves only the keys of one arc of the ring.
Statement II: With placement by key mod n, changing n from 3 to 4 leaves most keys on their old nodes.
(1) Both Statement I and Statement II are true  (2) Both Statement I and Statement II are false  (3) Statement I is true but Statement II is false  (4) Statement I is false but Statement II is true
