// Copyright 2019-2022 CEA LIST
// SPDX-FileCopyrightText: 2019-2022 CEA LIST <gael.de-chalendar@cea.fr>
//
// SPDX-License-Identifier: MIT

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
#include "Doc.h"
#include "Doc_private.h"
#include "Token.h"
#include "common/AbstractFactoryPattern/AmosePluginsManager.h"
#include "common/LimaCommon.h"
#include "common/LimaVersion.h"
#include "common/Data/strwstrtools.h"
#include "common/MediaticData/mediaticData.h"
#include "common/MediaProcessors/MediaProcessUnit.h"
#include <common/ProcessUnitFramework/AnalysisContent.h>
#include "common/QsLog/QsLog.h"
#include "common/QsLog/QsLogDest.h"
#include "common/QsLog/QsLogCategories.h"
#include "common/QsLog/QsDebugOutput.h"
#include "common/XMLConfigurationFiles/xmlConfigurationFileParser.h"
#include "common/time/traceUtils.h"
#include "common/tools/FileUtils.h"
#include "common/tools/LimaMainTaskRunner.h"

#include "linguisticProcessing/common/linguisticData/languageData.h"
#include <linguisticProcessing/common/linguisticData/LimaStringText.h>
#include "linguisticProcessing/client/LinguisticProcessingClientFactory.h"
#include "linguisticProcessing/client/AnalysisHandlers/BowTextWriter.h"
#include "linguisticProcessing/client/AnalysisHandlers/BowTextHandler.h"
#include "linguisticProcessing/client/AnalysisHandlers/SimpleStreamHandler.h"
#include "linguisticProcessing/client/AnalysisHandlers/LTRTextHandler.h"
#include "linguisticProcessing/core/EventAnalysis/EventHandler.h"
#include <linguisticProcessing/core/LinguisticAnalysisStructure/AnalysisGraph.h>
#include "linguisticProcessing/core/LinguisticProcessors/LinguisticMetaData.h"
#include "linguisticProcessing/core/LinguisticResources/AbstractResource.h"
#include "linguisticProcessing/core/LinguisticResources/LinguisticResources.h"

#include <deque>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <vector>

#include <QtCore/QCoreApplication>
#include <QtCore/QString>

#include <QtCore>

using namespace Lima::LinguisticProcessing;
using namespace Lima::Common::MediaticData;
using MedData = Lima::Common::MediaticData::MediaticData ;
using namespace Lima::Common::Misc;
using namespace Lima;


std::shared_ptr< std::ostringstream > openHandlerOutputString(
    AbstractTextualAnalysisHandler* handler,
    const std::set<std::string>&dumpers,
    const std::string& dumperId);
Doc docFrom_analysis(std::shared_ptr<Lima::AnalysisContent> analysis);
int run(int aargc,char** aargv);

class LimaAnalyzerPrivate
{
  friend class LimaAnalyzer;
public:
  LimaAnalyzerPrivate(const QStringList& qlangs,
                      const QStringList& qpipelines,
                      const QString& modulePath,
                      const QString& user_config_path,
                      const QString& user_resources_path,
                      const QString& meta);
  ~LimaAnalyzerPrivate() {}
  LimaAnalyzerPrivate(const LimaAnalyzerPrivate& a) = delete;
  LimaAnalyzerPrivate& operator=(const LimaAnalyzerPrivate& a) = delete;

  const std::string analyzeText(const std::string& text,
                                const std::string& lang,
                                const std::string& pipeline,
                                const std::string& meta);

//   std::shared_ptr<Lima::AnalysisContent> operator()(const std::string& text,
//                                                     const std::string& lang="eng",
//                                                     const std::string& pipeline="main",
//                                                     const std::string& meta="") const;

  Doc operator()(const std::string& text,
                 const std::string& lang="eng",
                 const std::string& pipeline="main",
                 const std::string& meta="") const;

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

  // Store constructor parameters to be able to implement copy constructor
  QStringList qlangs;
  QStringList qpipelines;
  QString modulePath;
  QString user_config_path;
  QString user_resources_path;
  QString meta;
};


LimaAnalyzerPrivate::LimaAnalyzerPrivate(const QStringList& iqlangs,
                                         const QStringList& iqpipelines,
                                         const QString& imodulePath,
                                         const QString& iuser_config_path,
                                         const QString& iuser_resources_path,
                                         const QString& imeta) :
    qlangs(iqlangs), qpipelines(iqpipelines), modulePath(imodulePath),
    user_config_path(iuser_config_path), user_resources_path(iuser_resources_path), meta(imeta)
{
  int argc = 1;
  char* argv[2] = {(char*)("LimaAnalyzer"), NULL};
  QCoreApplication app(argc, argv);


  QStringList additionalPaths({modulePath+"/config"});
  // Add here LIMA_CONF content in front, otherwise it will be ignored
  auto limaConf = QString::fromUtf8(qgetenv("LIMA_CONF").constData());
  if (!limaConf.isEmpty())
    additionalPaths = limaConf.split(LIMA_PATH_SEPARATOR) + additionalPaths;
  // Add then the user path in front again such that it takes precedence on environment variable
  if (!user_config_path.isEmpty())
    additionalPaths.push_front(user_config_path);
  auto configDirs = buildConfigurationDirectoriesList(QStringList({"lima"}),
                                                      additionalPaths);
  auto configPath = configDirs.join(LIMA_PATH_SEPARATOR);

  QStringList additionalResourcePaths({modulePath+"/resources"});
  // Add here LIMA_RESOURCES content in front, otherwise it will be ignored
  auto limaRes = QString::fromUtf8(qgetenv("LIMA_RESOURCES").constData());
  if (!limaRes.isEmpty())
    additionalResourcePaths = limaRes.split(LIMA_PATH_SEPARATOR) + additionalResourcePaths;
  if (!user_resources_path.isEmpty())
    additionalResourcePaths.push_front(user_resources_path);
  auto resourcesDirs = buildResourcesDirectoriesList(QStringList({"lima"}),
                                                     additionalResourcePaths);
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

  std::vector<std::string> vinactiveUnits;
  std::string strConfigPath;

  // parse 'meta' argument to add metadata
  if(!meta.isEmpty())
  {
    std::string metaString(meta.toStdString());
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
        metaData.insert(std::make_pair(std::string(str,0,i),
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
  for (const auto & inactiveUnit: vinactiveUnits)
  {
    inactiveUnits.insert(inactiveUnit);
  }
  std::deque<std::string> pipelines;
  for (const auto& pipeline: qpipelines)
    pipelines.push_back(pipeline.toStdString());


  uint64_t beginTime=TimeUtils::getCurrentTime();

  std::deque<std::string> langs;
  for (const auto& lang: qlangs)
    langs.push_back(lang.toStdString());
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

LimaAnalyzer::LimaAnalyzer(const std::string& langs,
                           const std::string& pipelines,
                           const std::string& modulePath,
                           const std::string& user_config_path,
                           const std::string& user_resources_path,
                           const std::string& meta)
{
  QStringList qlangs = QString::fromStdString(langs).split(",");
  QStringList qpipelines = QString::fromStdString(pipelines).split(",");
  m_d = new LimaAnalyzerPrivate(qlangs, qpipelines,
                                QString::fromStdString(modulePath),
                                QString::fromStdString(user_config_path),
                                QString::fromStdString(user_resources_path),
                                QString::fromStdString(meta));
}

LimaAnalyzer::~LimaAnalyzer()
{
  delete m_d;
}

LimaAnalyzer::LimaAnalyzer(const LimaAnalyzer& a) :
    m_d(new LimaAnalyzerPrivate(a.m_d->qlangs, a.m_d->qpipelines,
                                a.m_d->modulePath,
                                a.m_d->user_config_path,
                                a.m_d->user_resources_path,
                                a.m_d->meta))
{
  std::cerr << "LimaAnalyzer::LimaAnalyzer copy constructor" << std::endl;
}

LimaAnalyzer& LimaAnalyzer::operator=(const LimaAnalyzer& a)
{
  std::cerr << "LimaAnalyzer::operator=" << std::endl;
  delete m_d;
  m_d = new LimaAnalyzerPrivate(a.m_d->qlangs, a.m_d->qpipelines,
                                a.m_d->modulePath,
                                a.m_d->user_config_path,
                                a.m_d->user_resources_path,
                                a.m_d->meta);
  return *this;
}

// LimaAnalyzer *LimaAnalyzer::clone()
// {
//     return new LimaAnalyzer(*this);
// }

Doc LimaAnalyzer::operator()(const std::string& text,
                                     const std::string& lang,
                                     const std::string& pipeline,
                                     const std::string& meta) const
{
  try
  {
    return (*m_d)(text, lang, pipeline, meta);
  }
  catch (const Lima::LinguisticProcessing::LinguisticProcessingException& e)
  {
    std::cerr << "LIMA internal error: " << e.what() << std::endl;
    return Doc();
  }
}

std::string LimaAnalyzer::analyzeText(const std::string& text,
                                    const std::string& lang,
                                    const std::string& pipeline,
                                    const std::string& meta) const
{
//   std::cerr << "LimaAnalyzer::analyzeText" << std::endl;
  try {
  return m_d->analyzeText(text, lang, pipeline, meta);
  }
  catch (const Lima::LinguisticProcessing::LinguisticProcessingException& e) {
    std::cerr << "LIMA internal error: " << e.what() << std::endl;
  }
  return "";
}

Doc LimaAnalyzerPrivate::operator()(
    const std::string& text,
    const std::string& lang,
    const std::string& pipeline,
    const std::string& meta) const
{
  auto localMetaData = metaData;
  localMetaData["FileName"]="param";
  auto qmeta = QString::fromStdString(meta).split(",");
  for (const auto& m: qmeta)
  {
    auto kv = m.split(":");
    if (kv.size() == 2)
      localMetaData[kv[0].toStdString()] = kv[1].toStdString();
  }

  localMetaData["Lang"]=lang;

  QString contentText = QString::fromUtf8(text.c_str());
  if (contentText.isEmpty())
  {
    std::cerr << "Empty input ! " << std::endl;
    return Doc();
  }
  else
  {
    // analyze it
//       std::cerr << "Analyzing " << contentText.toStdString() << std::endl;
    try
    {
      auto analysis = m_client->analyze(contentText, localMetaData, pipeline, handlers, inactiveUnits);
      return docFrom_analysis(analysis);
    }
    catch (const Lima::LimaException& e)
    {
      std::cerr << "Lima internal error: " << e.what() << std::endl;
      return Doc();
    }
  }
}

const std::string LimaAnalyzerPrivate::analyzeText(const std::string& text,
                                    const std::string& lang,
                                    const std::string& pipeline,
                                    const std::string& meta)
{
  auto txtofs  = openHandlerOutputString(simpleStreamHandler, dumpers, "text");

  auto localMetaData = metaData;
  localMetaData["FileName"]="param";
  auto qmeta = QString::fromStdString(meta).split(",");
  for (const auto& m: qmeta)
  {
    auto kv = m.split(":");
    if (kv.size() == 2)
      localMetaData[kv[0].toStdString()] = kv[1].toStdString();
  }

  localMetaData["Lang"]=lang;

  if (splitMode == std::string("lines"))
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
      try {
        m_client->analyze(contentText,
                        localMetaData,
                        pipeline,
                        handlers,
                        inactiveUnits);
      } catch (const Lima::LimaException& e) {
        std::cerr << "Lima internal error: " << e.what() << std::endl;
        return txtofs->str();
      }
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
      try {
        m_client->analyze(contentText, localMetaData, pipeline, handlers,
                          inactiveUnits);
      } catch (const Lima::LimaException& e) {
        std::cerr << "Lima internal error: " << e.what() << std::endl;
        return txtofs->str();
      }
    }
  }

  return txtofs->str();
}

std::shared_ptr< std::ostringstream > openHandlerOutputString(
    AbstractTextualAnalysisHandler* handler,
    const std::set<std::string>&dumpers,
    const std::string& dumperId)
{
  auto ofs = std::make_shared< std::ostringstream >();
  if (dumpers.find(dumperId)!=dumpers.end())
  {
    handler->setOut(ofs.get());
  }
  return ofs;
}


Doc docFrom_analysis(std::shared_ptr<Lima::AnalysisContent> analysis)
{
  auto metadataholder = static_cast<LinguisticMetaData*>(analysis->getData("LinguisticMetaData"));
  const auto& lang = metadataholder->getMetaData("Lang");
  auto medId = MedData::single().media(lang);
  const auto& languageData = static_cast<const LanguageData&>(MedData::single().mediaData(medId));
  const auto& propertyCodeManager = languageData.getPropertyCodeManager();
  const auto& propertyAccessor = propertyCodeManager.getPropertyAccessor("MICRO");

  // std::cerr << "docFrom_analysis" << std::endl;
  Doc doc;
  auto sp = &MedData::single().stringsPool(MedData::single().media(lang));

  doc.m_d->analysis = analysis;
  auto anaGraphData = static_cast<LinguisticAnalysisStructure::AnalysisGraph*>(analysis->getData("AnalysisGraph"));
  auto anaGraph = anaGraphData->getGraph();
  auto posGraphData = static_cast<LinguisticAnalysisStructure::AnalysisGraph*>(analysis->getData("PosGraph"));
  auto posGraph = posGraphData->getGraph();
  auto firstVertex = posGraphData->firstVertex();
  auto lastVertex = posGraphData->lastVertex();
  auto v = firstVertex;
  auto [it, it_end] = boost::out_edges(v, *posGraph);
  if (it != it_end)
  {
      v = boost::target(*it, *posGraph);
  }
  else
  {
      v = lastVertex;
  }
  auto i = 0;
  auto tokens = get(vertex_token, *posGraph);
  auto morphoDatas = get(vertex_data, *posGraph);
  // std::cerr << "docFrom_analysis before while" << std::endl;
  while (v != lastVertex)
  {
    // std::cerr << "docFrom_analysis on vertex " << v << posGraph << std::endl;
    auto ft = tokens[v];
    auto morphoData = morphoDatas[v];

    auto inflectedToken = ft->stringForm().toStdString();
    auto lemmatizedToken = (*sp)[(*morphoData)[0].lemma].toStdString();
    // std::cerr << "docFrom_analysis token/lemma are " << inflectedToken << "/" << lemmatizedToken << std::endl;

    auto pos = ft->position();
    auto len = ft->length();
    // std::cerr << "docFrom_analysis pos/len are " << pos << "/" << len << std::endl;
    auto micro = languageData.getPropertyCodeManager()
                    .getPropertyManager("MICRO")
                    .getPropertySymbolicValue(morphoData->firstValue(propertyAccessor));

    Token t(len, inflectedToken, lemmatizedToken, i++, pos, micro, 0, "");
    // std::cerr << "docFrom_analysis pushing token" << std::endl;
    doc.m_d->tokens.push_back(t);

    auto [it, it_end] = boost::out_edges(v, *posGraph);
    if (it != it_end)
    {
        v = boost::target(*it, *posGraph);
    }
    else
    {
        v = lastVertex;
    }

  }
  // std::cerr << "docFrom_analysis before return" << std::endl;
  return doc;
}
