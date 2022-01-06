/****************************************************************************
**
** Copyright (C) 2018 The Qt Company Ltd.
** Contact: https://www.qt.io/licensing/
**
** This file is part of the Qt for Python examples of the Qt Toolkit.
**
** $QT_BEGIN_LICENSE:BSD$
** Commercial License Usage
** Licensees holding valid commercial Qt licenses may use this file in
** accordance with the commercial license agreement provided with the
** Software or, alternatively, in accordance with the terms contained in
** a written agreement between you and The Qt Company. For licensing terms
** and conditions see https://www.qt.io/terms-conditions. For further
** information use the contact form at https://www.qt.io/contact-us.
**
** BSD License Usage
** Alternatively, you may use this file under the terms of the BSD license
** as follows:
**
** "Redistribution and use in source and binary forms, with or without
** modification, are permitted provided that the following conditions are
** met:
**   * Redistributions of source code must retain the above copyright
**     notice, this list of conditions and the following disclaimer.
**   * Redistributions in binary form must reproduce the above copyright
**     notice, this list of conditions and the following disclaimer in
**     the documentation and/or other materials provided with the
**     distribution.
**   * Neither the name of The Qt Company Ltd nor the names of its
**     contributors may be used to endorse or promote products derived
**     from this software without specific prior written permission.
**
**
** THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
** "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
** LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
** A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
** OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
** SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
** LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
** DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
** THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
** (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
** OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
**
** $QT_END_LICENSE$
**
****************************************************************************/

#include "lima.h"
#include "common/LimaCommon.h"
#include "common/LimaVersion.h"
#include "common/tools/LimaMainTaskRunner.h"
#include "common/MediaticData/mediaticData.h"
#include "common/MediaProcessors/MediaProcessUnit.h"
#include "common/XMLConfigurationFiles/xmlConfigurationFileParser.h"
#include "common/Data/strwstrtools.h"
#include "common/time/traceUtils.h"
#include "common/tools/FileUtils.h"
#include "common/QsLog/QsLog.h"
#include "common/QsLog/QsLogDest.h"
#include "common/QsLog/QsLogCategories.h"
#include "common/QsLog/QsDebugOutput.h"
#include "common/AbstractFactoryPattern/AmosePluginsManager.h"

#include "linguisticProcessing/common/linguisticData/languageData.h"
#include "linguisticProcessing/client/LinguisticProcessingClientFactory.h"
#include "linguisticProcessing/client/AnalysisHandlers/BowTextWriter.h"
#include "linguisticProcessing/client/AnalysisHandlers/BowTextHandler.h"
#include "linguisticProcessing/client/AnalysisHandlers/SimpleStreamHandler.h"
#include "linguisticProcessing/client/AnalysisHandlers/LTRTextHandler.h"
#include "linguisticProcessing/core/EventAnalysis/EventHandler.h"
#include "linguisticProcessing/core/LinguisticResources/AbstractResource.h"
#include "linguisticProcessing/core/LinguisticResources/LinguisticResources.h"

#include <string>
#include <vector>
#include <iostream>
#include <iomanip>
#include <fstream>

#include <QtCore/QCoreApplication>
#include <QtCore/QString>
#include <QtCore/QStringRef>

#include <QtCore>

using namespace Lima::LinguisticProcessing;
using namespace Lima::Common::MediaticData;
using namespace Lima::Common::Misc;
using namespace Lima;

std::ostream* openHandlerOutputFile(AbstractTextualAnalysisHandler* handler,
                                    const std::string& fileName,
                                    const std::set< std::string >& dumpers,
                                    const std::string& dumperId);
void closeHandlerOutputFile(std::ostream* ofs);
int run(int aargc,char** aargv);

class LimaAnalyzerPrivate
{
  friend class LimaAnalyzer;
public:
  LimaAnalyzerPrivate(const QString& modulePath);
  ~LimaAnalyzerPrivate() {}
  LimaAnalyzerPrivate(const LimaAnalyzerPrivate& a){}
  LimaAnalyzerPrivate& operator=(const LimaAnalyzerPrivate& a){}

  const std::string analyzeText(const std::string& text,
                                const std::string& lang,
                                const std::string& pipeline);

  std::shared_ptr< AbstractLinguisticProcessingClient > m_client;
  std::map<std::string,std::string> metaData;
  std::string splitMode;
  std::map<std::string, AbstractAnalysisHandler*> handlers;
  std::set<std::string> inactiveUnits;


  BowTextWriter* bowTextWriter = 0;
  EventAnalysis::EventHandler* eventHandler = 0;
  BowTextHandler* bowTextHandler = 0;
  SimpleStreamHandler* simpleStreamHandler = 0;
  SimpleStreamHandler* fullXmlSimpleStreamHandler = 0;
  LTRTextHandler* ltrTextHandler=0;


  std::set<std::string> dumpers = {"text"};

};


LimaAnalyzerPrivate::LimaAnalyzerPrivate(const QString& modulePath)
{
  int argc = 1;
  char* argv[2] = {(char*)("LimaAnalyzer"), NULL};
  QCoreApplication app(argc, argv);
//   VIRTUAL_ENV/lib/python3.8/site-packages/aymara/config/
//   /opt/_internal/cpython-3.8.12/lib/python3.8/site-packages/aymara
//   std::cerr << "LimaAnalyzerPrivate::LimaAnalyzerPrivate() "
//             << QCoreApplication::applicationDirPath().toStdString()
//             << " --- "
//             << QCoreApplication::applicationName().toStdString()
//             << " --- "
//             << modulePath.toStdString()
//             << std::endl;
//   auto appName = QCoreApplication::applicationName();
//   QStringList filters({"python*"});
//   auto dir = QDir(QCoreApplication::applicationDirPath());
//   dir.cdUp();
//   dir.cd("lib");
//   dir.cd(appName);
//   dir.cd("site-packages");
//   dir.cd("aymara");
//   QString d = dir.absolutePath();
  auto configDirs = buildConfigurationDirectoriesList(QStringList({"lima"}),
                                                      QStringList({modulePath+"/config"}));
  auto configPath = configDirs.join(LIMA_PATH_SEPARATOR);

  auto resourcesDirs = buildResourcesDirectoriesList(QStringList({"lima"}),
                                                     QStringList(modulePath+"/resources"));
  auto resourcesPath = resourcesDirs.join(LIMA_PATH_SEPARATOR);

  QsLogging::initQsLog(configPath);
//   std::cerr << "QsLog initialized" << std::endl;
  // Necessary to initialize factories
  Lima::AmosePluginsManager::single();
//   std::cerr << "LimaAnalyzerPrivate::LimaAnalyzerPrivate() plugins manager created" << std::endl;
  if (!Lima::AmosePluginsManager::changeable().loadPlugins(configPath))
  {
    throw InvalidConfiguration("loadLibrary method failed.");
  }
//   std::cerr << "Amose plugins are now initialized hop" << std::endl;
//   qDebug() << "Amose plugins are now initialized";


  std::string lpConfigFile = "lima-analysis.xml";
  std::string commonConfigFile = "lima-common.xml";
  std::string clientId = "lima-coreclient";
  std::vector<std::string> languages;
  std::vector<std::string> dumpersv;

  std::string pipeline = "main";
  std::vector<std::string> files;
  std::vector<std::string> vinactiveUnits;
  std::string meta;
  std::string strConfigPath;

  std::vector<std::pair<std::string,std::string> > userMetaData;
  // parse 'meta' argument to add metadata
  if(!meta.empty())
  {
    std::string metaString(meta);
    std::string::size_type k=0;
    do
    {
      k=metaString.find(",");
      //if (k==std::string::npos) continue;
      std::string str(metaString,0,k);
      std::string::size_type i=str.find(":");
      if (i==std::string::npos)
      {
        std::cerr << "meta argument '"<< str
                  << "' is not of the form XXX:YYY: ignored" << std::endl;
      }
      else
      {
        //std::cout << "add metadata " << std::string(str,0,i) << "=>" << std::string(str,i+1) << std::endl;
        userMetaData.push_back(std::make_pair(std::string(str,0,i),
                                              std::string(str,i+1)));
      }
      if (k!=std::string::npos)
      {
        metaString=std::string(metaString,k+1);
      }
    }
    while (k!=std::string::npos);
  }

  std::set<std::string> inactiveUnits;
  for (const auto & inactiveUnit : vinactiveUnits)
  {
    inactiveUnits.insert(inactiveUnit);
  }
  std::deque<std::string> pipelines;

  pipelines.push_back(pipeline);

  uint64_t beginTime=TimeUtils::getCurrentTime();

  std::deque<std::string> langs = {"fre", "eng"};
//   std::cerr << "LimaAnalyzerPrivate::LimaAnalyzerPrivate() "
//             << resourcesPath.toUtf8().constData() << ", "
//             << configPath.toUtf8().constData() << ", "
//             << commonConfigFile << ", "
//             << langs.front() << std::endl;
  // initialize common
  Common::MediaticData::MediaticData::changeable().init(
    resourcesPath.toUtf8().constData(),
    configPath.toUtf8().constData(),
    commonConfigFile,
    langs);
//   std::cerr << "MediaticData initialized" << std::endl;

  bool clientFactoryConfigured = false;
  Q_FOREACH(QString configDir, configDirs)
  {
    if (QFileInfo::exists(configDir + "/" + lpConfigFile.c_str()))
    {
//       std::cerr << "LimaAnalyzerPrivate::LimaAnalyzerPrivate() configuring "
//           << (configDir + "/" + lpConfigFile.c_str()).toUtf8().constData() << ", "
//           << clientId << std::endl;

      // initialize linguistic processing
      Lima::Common::XMLConfigurationFiles::XMLConfigurationFileParser lpconfig(
          (configDir + "/" + lpConfigFile.c_str()));
      LinguisticProcessingClientFactory::changeable().configureClientFactory(
        clientId,
        lpconfig,
        langs,
        pipelines);
      clientFactoryConfigured = true;
      break;
    }
  }
  if(!clientFactoryConfigured)
  {
    std::cerr << "No LinguisticProcessingClientFactory were configured with"
              << configDirs.join(LIMA_PATH_SEPARATOR).toStdString()
              << "and" << lpConfigFile << std::endl;
    throw LimaException("Configuration failure");
  }
//   std::cerr << "Client factory configured" << std::endl;

  m_client = std::shared_ptr< AbstractLinguisticProcessingClient >(
      std::dynamic_pointer_cast<AbstractLinguisticProcessingClient>(
          LinguisticProcessingClientFactory::single().createClient(clientId)));

  // Set the handlers

  std::set<std::string> dumpers({"text"});
//   if (dumpers.find("bow") != dumpers.end())
//   {
    bowTextWriter = new BowTextWriter();
    handlers.insert(std::make_pair("bowTextWriter",
                                   bowTextWriter));
//   }
//   if (dumpers.find("bowh") != dumpers.end())
//   {
    bowTextHandler = new BowTextHandler();
    handlers.insert(std::make_pair("bowTextHandler",
                                   bowTextHandler));
//   }
//   if (dumpers.find("text") != dumpers.end())
//   {
    simpleStreamHandler = new SimpleStreamHandler();
    handlers.insert(std::make_pair("simpleStreamHandler",
                                   simpleStreamHandler));
//   }
//   if (dumpers.find("fullxml") != dumpers.end())
//   {
    fullXmlSimpleStreamHandler = new SimpleStreamHandler();
    handlers.insert(std::make_pair("fullXmlSimpleStreamHandler",
                                   fullXmlSimpleStreamHandler));
//   }
//   if (dumpers.find("ltr") != dumpers.end())
//   {
    ltrTextHandler= new LTRTextHandler();
    handlers.insert(std::make_pair("ltrTextHandler",
                                   ltrTextHandler));
//   }

}

LimaAnalyzer::LimaAnalyzer(const std::string& modulePath) :
  m_d(new LimaAnalyzerPrivate(QString::fromStdString(modulePath)))
{
}

LimaAnalyzer::~LimaAnalyzer()
{
  delete m_d;
}

LimaAnalyzer::LimaAnalyzer(const LimaAnalyzer& a)
{
  std::cerr << "AAAaaaahh!" << std::endl;
}

LimaAnalyzer LimaAnalyzer::operator=(const LimaAnalyzer&_a)
{
  std::cerr << "BAAAaaaahh!" << std::endl;
  return *this;
}

LimaAnalyzer *LimaAnalyzer::clone()
{
    return new LimaAnalyzer(*this);
}

const std::string LimaAnalyzer::analyzeText(const std::string& text,
                                    const std::string& lang,
                                    const std::string& pipeline)
{
//   std::cerr << "LimaAnalyzer::analyzeText" << std::endl;
  try {
  return m_d->analyzeText(text, lang, pipeline);
  }
  catch (const Lima::LinguisticProcessing::LinguisticProcessingException& e) {
    std::cerr << "LIMA internal error: " << e.what() << std::endl;
  }
  return "";
}

const std::string LimaAnalyzerPrivate::analyzeText(const std::string& text,
                                    const std::string& lang,
                                    const std::string& pipeline)
{
  qDebug() << "LimaAnalyzerPrivate::analyzeText" << text << lang << pipeline;
//     ("output,o",
//    po::value< std::vector<std::string> >(&outputsv),
//    "where to write dumpers output. By default, each dumper writes its results on a file whose name is the input file with a predefined suffix  appended. This option allows to chose another suffix or to write on standard output. Its syntax  is the following: <dumper>:<destination> with <dumper> a  dumper name and destination, either the value 'stdout' or a suffix.")
  std::vector<std::string> outputsv;
  QMap< QString, QString > outputs;
  for(std::vector<std::string>::const_iterator outputsIt = outputsv.begin();
      outputsIt != outputsv.end(); outputsIt++)
  {
    QStringList output = QString::fromUtf8((*outputsIt).c_str()).split(":");
    if (output.size()==2)
    {
      outputs[output[0]] = output[1];
    }
    else
    {
      // Option syntax  error
      std::cerr << "syntax error in output setting:" << *outputsIt << std::endl;
    }
  }

  // set the output files (to 0 if not in list)
  // remember to call closeHandlerOutputFile for each call to openHandlerOutputFile
//   std::string file;
//   QString bowOut = outputs.contains("bow")
//       ? (outputs["bow"] == "stdout"
//           ? "stdout"
//           : QString::fromUtf8((file).c_str())+outputs["bow"])
//       : QString::fromUtf8((file).c_str())+".bin";
//   QString textOut = outputs.contains("text")
//       ? (outputs["text"] == "stdout"
//           ? "stdout"
//           : QString::fromUtf8((file).c_str())+outputs["text"])
//       : "stdout";
//   QString fullxmlOut = outputs.contains("fullxml")
//       ? (outputs["fullxml"] == "stdout"
//           ? "stdout"
//           : QString::fromStdString(file)+outputs["fullxml"])
//       : "stdout";

  QString bowOut = "stdout";
  QString textOut = "stdout";
  QString fullxmlOut = "stdout";
  auto bowofs  = openHandlerOutputFile(bowTextWriter,
                                        std::string(bowOut.toStdString()),
                                        dumpers,
                                        "bow");
  auto txtofs  = openHandlerOutputFile(simpleStreamHandler,
                                        std::string(textOut.toStdString()),
                                        dumpers,
                                        "text");
  auto fullxmlofs  = openHandlerOutputFile(fullXmlSimpleStreamHandler,
                                            std::string(fullxmlOut.toStdString()),
                                            dumpers,
                                            "fullxml");
  std::ostringstream oss;

  metaData["FileName"]="param";
  metaData["Lang"]=lang;

  if (splitMode == "lines")
  {
    QStringList allText = QString::fromUtf8(text.c_str()).split("\n");
    int lineNum = 0;
    int nbLines = allText.size();
//     std::cerr << "\rStarting analysis";
    for (const auto& contentText: allText)
    {
      lineNum++;
      QString percent = QString::number((lineNum*1.0/nbLines*100),'f',2);
      if ( (lineNum % 100) == 0)
      {
        std::cerr << "\rAnalyzed "<< lineNum << "/" << nbLines
                  << " (" << percent.toUtf8().constData() << "%) lines";
      }
      // analyze it
      m_client->analyze(contentText,
                      metaData,
                      pipeline,
                      handlers,
                      inactiveUnits);
    }
  }
  else // default == none
  {
    QString contentText = QString::fromUtf8(text.c_str());
    if (contentText.isEmpty())
    {
      std::cerr << "Empty input ! " << std::endl;
    }
    else
    {
      // analyze it
//       std::cerr << "Analyzing " << contentText.toStdString() << std::endl;
      m_client->analyze(contentText,metaData, pipeline, handlers, inactiveUnits);
    }
  }

  return oss.str();
}

std::ostream* openHandlerOutputFile(AbstractTextualAnalysisHandler* handler,
                                    const std::string& fileName,
                                    const std::set<std::string>&dumpers,
                                    const std::string& dumperId)
{
  std::ostream* ofs = nullptr;
  if (dumpers.find(dumperId)!=dumpers.end())
  {
    if (fileName=="stdout")
    {
      ofs = &std::cout;
    }
    else
    {
      ofs = new std::ofstream(fileName.c_str(),
                              std::ios_base::out
                                | std::ios_base::binary
                                | std::ios_base::trunc);
    }
    if (ofs->good())
    {
      handler->setOut(ofs);
    }
    else
    {
      std::cerr << "failed to open file " << fileName << std::endl;
      delete ofs; ofs = 0;
    }
  }
  return ofs;
}

void closeHandlerOutputFile(std::ostream* ofs)
{
  if (ofs != 0 && dynamic_cast<std::ofstream*>(ofs)!=0)
  {
    dynamic_cast<std::ofstream*>(ofs)->close();
    delete ofs;
    ofs = nullptr;
  }
}
