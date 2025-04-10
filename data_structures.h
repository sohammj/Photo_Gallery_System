#ifndef DATA_STRUCTURES_H
#define DATA_STRUCTURES_H

#include <iostream>
#include <string>
#include <ctime>

using namespace std;

// Node for linked list and tree
struct Node {
    string data;
    Node* next;
    Node* left;
    Node* right;

    Node(string d) : data(d), next(nullptr), left(nullptr), right(nullptr) {}
};

// Stack implementation using array
class Stack {
private:
    string items[50];
    int top;

public:
    Stack() : top(-1) {}

    bool isEmpty() { return top == -1; }
    void push(string item) { items[++top] = item; }
    string pop() { return items[top--]; }
    string peek() { return items[top]; }
};

// Queue implementation using array
class Queue {
private:
    string items[50];
    int front;
    int rear;

public:
    Queue() : front(0), rear(-1) {}

    bool isEmpty() { return front > rear; }
    void enqueue(string item) { items[++rear] = item; }
    string dequeue() { return items[front++]; }
    string peek() { return items[front]; }
};

// Tree implementation
class Tree {
private:
    Node* root;

    void insert(Node*& node, string data) {
        if (!node) {
            node = new Node(data);
            return;
        }
        if (data < node->data)
            insert(node->left, data);
        else
            insert(node->right, data);
    }

    void inorder(Node* node) {
        if (node) {
            inorder(node->left);
            cout << node->data << " ";
            inorder(node->right);
        }
    }

public:
    Tree() : root(nullptr) {}

    void insert(string data) { insert(root, data); }
    void inorder() { inorder(root); }
};

// Linked list implementation
class LinkedList {
private:
    Node* head;

public:
    LinkedList() : head(nullptr) {}

    void insert(string data) {
        Node* newNode = new Node(data);
        if (!head) {
            head = newNode;
        } else {
            Node* temp = head;
            while (temp->next)
                temp = temp->next;
            temp->next = newNode;
        }
    }

    void display() {
        Node* temp = head;
        while (temp) {
            cout << temp->data << " ";
            temp = temp->next;
        }
    }
};

// Simple array-based implementation for photos
class PhotoArray {
private:
    string photos[50];
    int count;

public:
    PhotoArray() : count(0) {}

    void add(string photo) {
        if (count < 50)
            photos[count++] = photo;
    }

    void display() {
        for (int i = 0; i < count; i++)
            cout << photos[i] << " ";
    }

    int getCount() { return count; }
    string getPhoto(int index) { return photos[index]; }
};

#endif // DATA_STRUCTURES_H