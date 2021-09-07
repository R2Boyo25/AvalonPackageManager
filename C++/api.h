#include <iostream>
#include <string>
#include <curl/curl.h>
using namespace std;

string data;

size_t writeCallback(char* buf, size_t size, size_t nmemb, void* up)
{
	for (int c = 0; c<size*nmemb; c++)
	{
		data.push_back(buf[c]);
	}
	return size*nmemb;
}

string GET()
{
	CURL* curl;

	curl_global_init(CURL_GLOBAL_ALL); //pretty obvious
	curl = curl_easy_init();

	curl_easy_setopt(curl, CURLOPT_URL, "http://www.cplusplus.com");
	curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, &writeCallback);
	curl_easy_setopt(curl, CURLOPT_VERBOSE, 1L);

	curl_easy_perform(curl);

	cout << endl << data << endl;
	cin.get();

	curl_easy_cleanup(curl);
	curl_global_cleanup();

	system("pause");
	return 0;
}