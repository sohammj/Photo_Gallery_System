#include <iostream>
#include <string>
#include <ctime>
#include "data_structures.h"

using namespace std;

// Simple Photo class
class Photo {
private:
    string filename;
    string location;
    time_t dateTime;
    string description;
    string tags[10];
    int viewCount;
    int fileSize;
    int tagCount;

public:
    Photo(const string& filename, const string& location, 
          time_t dateTime, const string& description, 
          const string tags[], int tagCount, int fileSize)
        : filename(filename), location(location), dateTime(dateTime), 
          description(description), viewCount(0), fileSize(fileSize), tagCount(tagCount) {
        for (int i = 0; i < tagCount; i++) {
            this->tags[i] = tags[i];
        }
    }

    string getFilename() const { return filename; }
    string getLocation() const { return location; }
    time_t getDateTime() const { return dateTime; }
    string getDescription() const { return description; }
    string getTags(int index) const { return tags[index]; }
    int getViewCount() const { return viewCount; }
    int getFileSize() const { return fileSize; }
    int getTagCount() const { return tagCount; }

    void incrementViewCount() { viewCount++; }
    void addTag(const string& tag) {
        for (int i = 0; i < tagCount; i++) {
            if (tags[i] == tag) return;
        }
        tags[tagCount] = tag;
        tagCount++;
    }
    bool hasTag(const string& tag) const {
        for (int i = 0; i < tagCount; i++) {
            if (tags[i] == tag) return true;
        }
        return false;
    }
};

// Photo Gallery System
class PhotoGallery {
private:
    Photo* photos[50];
    int photoCount;

public:
    PhotoGallery() : photoCount(0) {}

    int getCount() const { return photoCount; }

    void addPhoto(Photo* photo) {
        if (photoCount < 50) {
            photos[photoCount++] = photo;
        }
    }

    void viewPhoto(int index) {
        if (index >= 0 && index < photoCount) {
            photos[index]->incrementViewCount();
        }
    }

    void addTagToPhoto(int index, const string& tag) {
        if (index >= 0 && index < photoCount) {
            photos[index]->addTag(tag);
        }
    }

    void searchByLocation(const string& location) {
        cout << "\nSearch results for location '" << location << "':" << endl;
        for (int i = 0; i < photoCount; i++) {
            if (photos[i]->getLocation() == location) {
                displayPhoto(photos[i]);
            }
        }
    }

    void searchByTag(const string& tag) {
        cout << "\nSearch results for tag '" << tag << "':" << endl;
        for (int i = 0; i < photoCount; i++) {
            if (photos[i]->hasTag(tag)) {
                displayPhoto(photos[i]);
            }
        }
    }

    void searchByDateRange(time_t start, time_t end) {
        cout << "\nSearch results for date range:" << endl;
        for (int i = 0; i < photoCount; i++) {
            if (photos[i]->getDateTime() >= start && photos[i]->getDateTime() <= end) {
                displayPhoto(photos[i]);
            }
        }
    }

    void searchByTagPrefix(const string& prefix) {
        cout << "\nSearch results for keyword prefix '" << prefix << "':" << endl;
        for (int i = 0; i < photoCount; i++) {
            for (int j = 0; j < photos[i]->getTagCount(); j++) {
                if (photos[i]->getTags(j).find(prefix) == 0) {
                    displayPhoto(photos[i]);
                    break;
                }
            }
        }
    }

    void sortByDate() {
        for (int i = 0; i < photoCount - 1; i++) {
            for (int j = 0; j < photoCount - i - 1; j++) {
                if (photos[j]->getDateTime() < photos[j+1]->getDateTime()) {
                    swap(photos[j], photos[j+1]);
                }
            }
        }
        cout << "Photos sorted by date (newest first)." << endl;
    }

    void sortBySize() {
        for (int i = 0; i < photoCount - 1; i++) {
            for (int j = 0; j < photoCount - i - 1; j++) {
                if (photos[j]->getFileSize() < photos[j+1]->getFileSize()) {
                    swap(photos[j], photos[j+1]);
                }
            }
        }
        cout << "Photos sorted by size (largest first)." << endl;
    }

    void sortByPopularity() {
        for (int i = 0; i < photoCount - 1; i++) {
            for (int j = 0; j < photoCount - i - 1; j++) {
                if (photos[j]->getViewCount() < photos[j+1]->getViewCount()) {
                    swap(photos[j], photos[j+1]);
                }
            }
        }
        cout << "Photos sorted by popularity (most viewed first)." << endl;
    }

    void displayAllPhotos() {
        cout << "\nAll photos:" << endl;
        for (int i = 0; i < photoCount; i++) {
            displayPhoto(photos[i]);
        }
    }

    void displayPhoto(const Photo* photo) {
        cout << "Filename: " << photo->getFilename() << endl;
        cout << "Location: " << photo->getLocation() << endl;
        time_t dateTime = photo->getDateTime();
        cout << "Date: " << ctime(&dateTime);
        cout << "Description: " << photo->getDescription() << endl;
        
        cout << "Tags: ";
        for (int i = 0; i < photo->getTagCount(); i++) {
            if (i > 0) cout << ", ";
            cout << photo->getTags(i);
        }
        cout << endl;
        
        cout << "Views: " << photo->getViewCount() << endl;
        cout << "Size: " << photo->getFileSize() << " KB" << endl;
        cout << "------------------------------------" << endl;
    }

    Photo* getPhoto(int index) {
        if (index >= 0 && index < photoCount)
            return photos[index];
        return nullptr;
    }
};

// Helper functions
time_t stringToTime(const string& dateString) {
    struct tm tm = {};
    tm.tm_year = stoi(dateString.substr(0,4)) - 1900;
    tm.tm_mon = stoi(dateString.substr(5,2)) - 1;
    tm.tm_mday = stoi(dateString.substr(8,2));
    return mktime(&tm);
}

string timeToString(time_t time) {
    char buffer[80];
    struct tm* timeinfo = localtime(&time);
    strftime(buffer, sizeof(buffer), "%Y-%m-%d", timeinfo);
    return string(buffer);
}

// Backtracking algorithm to find all possible tag combinations
void findTagCombinations(Photo* photo, int index, string current, string combinations[]) {
    if (index == photo->getTagCount()) {
        combinations[index] = current;
        return;
    }
    findTagCombinations(photo, index + 1, current + " " + photo->getTags(index), combinations);
    findTagCombinations(photo, index + 1, current, combinations);
}

int main() {
    PhotoGallery gallery;
    PhotoArray photoArray;
    Tree tagTree;
    LinkedList locationList;
    Stack viewStack;
    Queue addQueue;

    // Add sample photos
    string tags1[] = {"vacation", "paris", "landmark"};
    Photo* photo1 = new Photo("vacation1.jpg", "Paris", stringToTime("2023-06-15"), 
                             "Eiffel Tower at sunset", tags1, 3, 2500);
    gallery.addPhoto(photo1);
    photoArray.add("vacation1.jpg");
    tagTree.insert("vacation");
    locationList.insert("Paris");
    viewStack.push("vacation1.jpg");
    addQueue.enqueue("vacation1.jpg");

    string tags2[] = {"family", "dinner", "home"};
    Photo* photo2 = new Photo("family1.jpg", "Home", stringToTime("2023-05-20"), 
                             "Family dinner", tags2, 3, 1800);
    gallery.addPhoto(photo2);
    photoArray.add("family1.jpg");
    tagTree.insert("family");
    locationList.insert("Home");
    viewStack.push("family1.jpg");
    addQueue.enqueue("family1.jpg");

    string tags3[] = {"pet", "dog", "park"};
    Photo* photo3 = new Photo("pet1.jpg", "Park", stringToTime("2023-07-10"), 
                             "My dog playing in the park", tags3, 3, 2200);
    gallery.addPhoto(photo3);
    photoArray.add("pet1.jpg");
    tagTree.insert("pet");
    locationList.insert("Park");
    viewStack.push("pet1.jpg");
    addQueue.enqueue("pet1.jpg");

    string tags4[] = {"vacation", "rome", "landmark"};
    Photo* photo4 = new Photo("vacation2.jpg", "Rome", stringToTime("2023-06-18"), 
                             "Colosseum tour", tags4, 3, 3000);
    gallery.addPhoto(photo4);
    photoArray.add("vacation2.jpg");
    tagTree.insert("rome");
    locationList.insert("Rome");
    viewStack.push("vacation2.jpg");
    addQueue.enqueue("vacation2.jpg");

    string tags5[] = {"work", "team", "office"};
    Photo* photo5 = new Photo("work1.jpg", "Office", stringToTime("2023-04-25"), 
                             "Team building event", tags5, 3, 1500);
    gallery.addPhoto(photo5);
    photoArray.add("work1.jpg");
    tagTree.insert("work");
    locationList.insert("Office");
    viewStack.push("work1.jpg");
    addQueue.enqueue("work1.jpg");

    // Simple menu
    int choice;
    bool running = true;
    
    while (running) {
        cout << "\n==== Photo Gallery System ====" << endl;
        cout << "1. View all photos" << endl;
        cout << "2. View a specific photo" << endl;
        cout << "3. Add a new photo" << endl;
        cout << "4. Search by location" << endl;
        cout << "5. Search by tag" << endl;
        cout << "6. Search by date range" << endl;
        cout << "7. Search by keyword prefix" << endl;
        cout << "8. Sort by date" << endl;
        cout << "9. Sort by size" << endl;
        cout << "10. Sort by popularity" << endl;
        cout << "11. Display data structures" << endl;
        cout << "0. Exit" << endl;
        cout << "Enter choice: ";
        cin >> choice;
        cin.ignore();
        
        switch (choice) {
            case 0:
                running = false;
                break;
                
            case 1:
                gallery.displayAllPhotos();
                break;
                
            case 2: {
                int index;
                cout << "Enter photo index (0-" << gallery.getCount() - 1 << "): ";
                cin >> index;
                cin.ignore();
                if (index >= 0 && index < gallery.getCount()) {
                    gallery.viewPhoto(index);
                    gallery.displayPhoto(gallery.getPhoto(index));
                } else {
                    cout << "Invalid index." << endl;
                }
                break;
            }
                
            case 3: {
                string filename, location, dateStr, description;
                string tags[10];
                int tagCount = 0;
                int fileSize;
                
                cout << "Enter filename: ";
                getline(cin, filename);
                
                cout << "Enter location: ";
                getline(cin, location);
                
                cout << "Enter date (YYYY-MM-DD): ";
                getline(cin, dateStr);
                
                cout << "Enter description: ";
                getline(cin, description);
                
                cout << "Enter tags (comma separated, max 10): ";
                string tagInput;
                getline(cin, tagInput);
                
                // Simple tag parsing
                size_t pos = 0;
                string token;
                while ((pos = tagInput.find(',')) != string::npos && tagCount < 10) {
                    token = tagInput.substr(0, pos);
                    tags[tagCount++] = token;
                    tagInput.erase(0, pos + 1);
                }
                if (!tagInput.empty() && tagCount < 10) {
                    tags[tagCount++] = tagInput;
                }
                
                cout << "Enter file size (KB): ";
                cin >> fileSize;
                cin.ignore();
                
                Photo* newPhoto = new Photo(filename, location, stringToTime(dateStr), description, tags, tagCount, fileSize);
                gallery.addPhoto(newPhoto);
                photoArray.add(filename);
                tagTree.insert(tags[0]);
                locationList.insert(location);
                viewStack.push(filename);
                addQueue.enqueue(filename);
                
                cout << "Photo added successfully." << endl;
                break;
            }
                
            case 4: {
                string location;
                cout << "Enter location to search: ";
                getline(cin, location);
                gallery.searchByLocation(location);
                break;
            }
                
            case 5: {
                string tag;
                cout << "Enter tag to search: ";
                getline(cin, tag);
                gallery.searchByTag(tag);
                break;
            }
                
            case 6: {
                string startDateStr, endDateStr;
                cout << "Enter start date (YYYY-MM-DD): ";
                getline(cin, startDateStr);
                
                cout << "Enter end date (YYYY-MM-DD): ";
                getline(cin, endDateStr);
                
                time_t startDate = stringToTime(startDateStr);
                time_t endDate = stringToTime(endDateStr);
                
                gallery.searchByDateRange(startDate, endDate);
                break;
            }
                
            case 7: {
                string prefix;
                cout << "Enter keyword prefix to search: ";
                getline(cin, prefix);
                gallery.searchByTagPrefix(prefix);
                break;
            }
                
            case 8:
                gallery.sortByDate();
                break;
                
            case 9:
                gallery.sortBySize();
                break;
                
            case 10:
                gallery.sortByPopularity();
                break;
                
            case 11: {
                cout << "\nData Structures:" << endl;
                cout << "Photo Array: ";
                photoArray.display();
                cout << "\nTag Tree: ";
                tagTree.inorder();
                cout << "\nLocation List: ";
                locationList.display();
                cout << "\nView Stack: ";
                Stack tempStack = viewStack;
                while (!tempStack.isEmpty()) {
                    cout << tempStack.peek() << " ";
                    tempStack.pop();
                }
                cout << "\nAdd Queue: ";
                Queue tempQueue = addQueue;
                while (!tempQueue.isEmpty()) {
                    cout << tempQueue.peek() << " ";
                    tempQueue.dequeue();
                }
                cout << endl;
                break;
            }
                
            default:
                cout << "Invalid choice. Please try again." << endl;
        }
    }
    
    cout << "Thank you for using Photo Gallery System!" << endl;
    return 0;
}