package main

import (
	"encoding/xml"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"path/filepath"
)

type Browsers struct {
	XMLName  xml.Name  `xml:"browsers"`
	Browsers []Browser `xml:"browser"`
}

type Browser struct {
	Name     string    `xml:"name,attr"`
	Versions []Version `xml:"version"`
}

type Version struct {
	Number  string   `xml:"number,attr"`
	Regions []Region `xml:"region"`
}

type Region struct {
	Name  string `xml:"name,attr"`
	Hosts []Host `xml:"host"`
}

type Host struct {
	Name     string `xml:"name,attr"`
	Port     string `xml:"port,attr"`
	Count    string `xml:"count,attr"`
	Username string `xml:"username,attr"`
	Password string `xml:"password,attr"`
	Scheme   string `xml:"scheme,attr"`
	VNC      string `xml:"vnc,attr"`
}

var (
	XMLDirectory = "xml" // Директория, где хранятся XML-файлы
)

func main() {
	http.HandleFunc("/", indexHandler)
	http.HandleFunc("/management", managementHandler)
	http.HandleFunc("/add_section", addSectionHandler)
	http.HandleFunc("/remove_section", removeSectionHandler)
	http.HandleFunc("/remove_host", removeHostHandler)
	http.HandleFunc("/logout", logoutHandler)

	log.Println("Сервер запущен на порту :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func indexHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == "GET" {
		http.ServeFile(w, r, "index.html")
	} else {
		http.Redirect(w, r, "/management", http.StatusFound)
	}
}

func managementHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == "GET" {
		http.ServeFile(w, r, "management.html")
	} else {
		http.Redirect(w, r, "/management", http.StatusFound)
	}
}

func addSectionHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == "POST" {
		browser := r.FormValue("browser")
		version := r.FormValue("version")
		region := r.FormValue("region")

		xmlFilePath := getXMLFilePath("user.xml")

		// Загрузка XML-файла
		xmlData, err := ioutil.ReadFile(xmlFilePath)
		if err != nil {
			log.Println("Ошибка при чтении XML-файла:", err)
			http.Redirect(w, r, "/management", http.StatusFound)
			return
		}

		// Декодирование XML-файла
		var browsers Browsers
		err = xml.Unmarshal(xmlData, &browsers)
		if err != nil {
			log.Println("Ошибка при декодировании XML:", err)
			http.Redirect(w, r, "/management", http.StatusFound)
			return
		}

		// Проверка наличия браузера и версии
		found := false
		for _, b := range browsers.Browsers {
			if b.Name == browser {
				for _, v := range b.Versions {
					if v.Number == version {
						found = true
						break
					}
				}
				break
			}
		}

		// Добавление раздела
		if !found {
			b := Browser{Name: browser}
			v := Version{Number: version}
			r := Region{Name: region}
			v.Regions = append(v.Regions, r)
			b.Versions = append(b.Versions, v)
			browsers.Browsers = append(browsers.Browsers, b)
		}

		// Кодирование XML-файла
		xmlData, err = xml.MarshalIndent(browsers, "", "  ")
		if err != nil {
			log.Println("Ошибка при кодировании XML:", err)
			http.Redirect(w, r, "/management", http.StatusFound)
			return
		}

		// Запись XML-данных в файл
		err = ioutil.WriteFile(xmlFilePath, xmlData, 0644)
		if err != nil {
			log.Println("Ошибка при записи XML-данных в файл:", err)
			http.Redirect(w, r, "/management", http.StatusFound)
			return
		}

		http.Redirect(w, r, "/management", http.StatusFound)
	}
}

func removeSectionHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == "POST" {
		browser := r.FormValue("browser")
		version := r.FormValue("version")
		region := r.FormValue("region")

		xmlFilePath := getXMLFilePath("user.xml")

		// Загрузка XML-файла
		xmlData, err := ioutil.ReadFile(xmlFilePath)
		if err != nil {
			log.Println("Ошибка при чтении XML-файла:", err)
			http.Redirect(w, r, "/management", http.StatusFound)
			return
		}

		// Декодирование XML-файла
		var browsers Browsers
		err = xml.Unmarshal(xmlData, &browsers)
		if err != nil {
			log.Println("Ошибка при декодировании XML:", err)
			http.Redirect(w, r, "/management", http.StatusFound)
			return
		}

		// Удаление раздела
		updatedBrowsers := removeSection(browser, version, region, browsers.Browsers)
		if updatedBrowsers == nil {
			log.Println("Не удалось найти раздел для удаления")
			http.Redirect(w, r, "/management", http.StatusFound)
			return
		}

		// Кодирование XML-файла
		xmlData, err = xml.MarshalIndent(updatedBrowsers, "", "  ")
		if err != nil {
			log.Println("Ошибка при кодировании XML:", err)
			http.Redirect(w, r, "/management", http.StatusFound)
			return
		}

		// Запись XML-данных в файл
		err = ioutil.WriteFile(xmlFilePath, xmlData, 0644)
		if err != nil {
			log.Println("Ошибка при записи XML-данных в файл:", err)
			http.Redirect(w, r, "/management", http.StatusFound)
			return
		}

		http.Redirect(w, r, "/management", http.StatusFound)
	}
}

func removeHostHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == "POST" {
		browser := r.FormValue("browser")
		version := r.FormValue("version")
		region := r.FormValue("region")
		host := r.FormValue("host")

		xmlFilePath := getXMLFilePath("user.xml")

		// Загрузка XML-файла
		xmlData, err := ioutil.ReadFile(xmlFilePath)
		if err != nil {
			log.Println("Ошибка при чтении XML-файла:", err)
			http.Redirect(w, r, "/management", http.StatusFound)
			return
		}

		// Декодирование XML-файла
		var browsers Browsers
		err = xml.Unmarshal(xmlData, &browsers)
		if err != nil {
			log.Println("Ошибка при декодировании XML:", err)
			http.Redirect(w, r, "/management", http.StatusFound)
			return
		}

		// Удаление хоста
		updatedBrowsers := removeHost(browser, version, region, host, browsers.Browsers)
		if updatedBrowsers == nil {
			log.Println("Не удалось найти хост для удаления")
			http.Redirect(w, r, "/management", http.StatusFound)
			return
		}

		// Кодирование XML-файла
		xmlData, err = xml.MarshalIndent(updatedBrowsers, "", "  ")
		if err != nil {
			log.Println("Ошибка при кодировании XML:", err)
			http.Redirect(w, r, "/management", http.StatusFound)
			return
		}

		// Запись XML-данных в файл
		err = ioutil.WriteFile(xmlFilePath, xmlData, 0644)
		if err != nil {
			log.Println("Ошибка при записи XML-данных в файл:", err)
			http.Redirect(w, r, "/management", http.StatusFound)
			return
		}

		http.Redirect(w, r, "/management", http.StatusFound)
	}
}

func logoutHandler(w http.ResponseWriter, r *http.Request) {
	http.Redirect(w, r, "/", http.StatusFound)
}

func getXMLFilePath(filename string) string {
	return filepath.Join(XMLDirectory, filename)
}

func removeSection(browser, version, region string, browsers []Browser) []Browser {
	// Поиск браузера
	for i, b := range browsers {
		if b.Name == browser {
			// Поиск версии
			for j, v := range b.Versions {
				if v.Number == version {
					// Поиск региона
					for k, r := range v.Regions {
						if r.Name == region {
							// Удаление региона
							v.Regions = append(v.Regions[:k], v.Regions[k+1:]...)

							// Если все регионы удалены, удалить версию
							if len(v.Regions) == 0 {
								b.Versions = append(b.Versions[:j], b.Versions[j+1:]...)
							}

							// Если все версии удалены, удалить браузер
							if len(b.Versions) == 0 {
								browsers = append(browsers[:i], browsers[i+1:]...)
							}

							return browsers
						}
					}
					break
				}
			}
			break
		}
	}
	return nil
}

func removeHost(browser, version, region, host string, browsers []Browser) []Browser {
	// Поиск браузера
	for i, b := range browsers {
		if b.Name == browser {
			// Поиск версии
			for j, v := range b.Versions {
				if v.Number == version {
					// Поиск региона
					for k, r := range v.Regions {
						if r.Name == region {
							// Поиск хоста
							for l, h := range r.Hosts {
								if h.Name == host {
									// Удаление хоста
									r.Hosts = append(r.Hosts[:l], r.Hosts[l+1:]...)

									// Если все хосты удалены, удалить регион
									if len(r.Hosts) == 0 {
										v.Regions = append(v.Regions[:k], v.Regions[k+1:]...)
									}

									// Если все регионы удалены, удалить версию
									if len(v.Regions) == 0 {
										b.Versions = append(b.Versions[:j], b.Versions[j+1:]...)
									}

									// Если все версии удалены, удалить браузер
									if len(b.Versions) == 0 {
										browsers = append(browsers[:i], browsers[i+1:]...)
									}

									return browsers
								}
							}
							break
						}
					}
					break
				}
			}
			break
		}
	}
	return nil
}
