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
#include "Span.h"
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

#include "linguisticProcessing/common/annotationGraph/AnnotationData.h"
#include "linguisticProcessing/common/linguisticData/languageData.h"
#include <linguisticProcessing/common/linguisticData/LimaStringText.h>
#include "linguisticProcessing/common/PropertyCode/PropertyCodeManager.h"
#include "linguisticProcessing/client/LinguisticProcessingClientFactory.h"
#include "linguisticProcessing/client/AnalysisHandlers/BowTextWriter.h"
#include "linguisticProcessing/client/AnalysisHandlers/BowTextHandler.h"
#include "linguisticProcessing/client/AnalysisHandlers/SimpleStreamHandler.h"
#include "linguisticProcessing/client/AnalysisHandlers/LTRTextHandler.h"
#include "linguisticProcessing/core/Automaton/SpecificEntityAnnotation.h"
#include "linguisticProcessing/core/EventAnalysis/EventHandler.h"
#include <linguisticProcessing/core/LinguisticAnalysisStructure/AnalysisGraph.h>
#include "linguisticProcessing/core/LinguisticAnalysisStructure/MorphoSyntacticData.h"
#include "linguisticProcessing/core/LinguisticProcessors/LinguisticMetaData.h"
#include "linguisticProcessing/core/LinguisticResources/AbstractResource.h"
#include "linguisticProcessing/core/LinguisticResources/LinguisticResources.h"
#include "linguisticProcessing/core/TextSegmentation/SegmentationData.h"
#include <deque>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <vector>

#include <boost/algorithm/string.hpp>
#include <boost/algorithm/string/find_format.hpp>
#include <boost/algorithm/string/finder.hpp>
#include <boost/format.hpp>

#include <QtCore/QCoreApplication>
#include <QtCore/QString>

#include <QtCore>

using namespace Lima::LinguisticProcessing;
using namespace Lima::LinguisticProcessing::SpecificEntities;
using namespace Lima::Common::AnnotationGraphs;
using namespace Lima::Common::MediaticData;
using LangData = Lima::Common::MediaticData::LanguageData;
using MedData = Lima::Common::MediaticData::MediaticData ;
using namespace Lima::Common::Misc;
using namespace Lima::Common::PropertyCode;
using namespace Lima;

struct character_escaper
{
    template<typename FindResultT>
    std::string operator()(const FindResultT& Match) const
    {
        std::string s;
        for (typename FindResultT::const_iterator i = Match.begin();
             i != Match.end();
             i++) {
            s += boost::str(boost::format("\\x%02x") % static_cast<int>(*i));
        }
        return s;
    }
};

std::shared_ptr< std::ostringstream > openHandlerOutputString(
    AbstractTextualAnalysisHandler* handler,
    const std::set<std::string>&dumpers,
    const std::string& dumperId);

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
  ~LimaAnalyzerPrivate() = default;
  LimaAnalyzerPrivate(const LimaAnalyzerPrivate& a) = delete;
  LimaAnalyzerPrivate& operator=(const LimaAnalyzerPrivate& a) = delete;

  const std::string analyzeText(const std::string& text,
                                const std::string& lang,
                                const std::string& pipeline,
                                const std::string& meta);

  Doc operator()(const std::string& text,
                 const std::string& lang="eng",
                 const std::string& pipeline="main",
                 const std::string& meta="");

  Doc docFrom_analysis(std::shared_ptr<Lima::AnalysisContent> analysis);

  int dumpPosGraphVertex(Doc& doc,
                         LinguisticGraphVertex v,
                         int& tokenId,
                         LinguisticGraphVertex vEndDone,
                         std::map<LinguisticGraphVertex,int>& segmentationMapping,
                         const QString& parentNeType,
                         bool first);

  int dumpAnalysisGraphVertex(Doc& doc,
                              LinguisticGraphVertex v,
                              LinguisticGraphVertex posGraphVertex,
                              int& tokenId,
                              LinguisticGraphVertex vEndDone,
                              const QString& neType,
                              bool first,
                              const Automaton::EntityFeatures& features);

  void dumpNamedEntity(Doc& doc,
                       LinguisticGraphVertex v,
                       int& tokenId,
                       LinguisticGraphVertex vEndDone,
                       std::map<LinguisticGraphVertex,int>& segmentationMapping,
                       const QString& neType);

  /** Gets the named entity type for the PosGraph vertex @ref posGraphVertex
   * if it is a specific entity. Return "_" otherwise
   */
  QString getNeType(LinguisticGraphVertex posGraphVertex);

  // std::pair<QString, QString> getConllRelName(
  //   LinguisticGraphVertex v,
  //   std::map<LinguisticGraphVertex,int>& segmentationMapping);

  const SpecificEntityAnnotation* getSpecificEntityAnnotation(
    LinguisticGraphVertex v) const;

  bool hasSpaceAfter(LinguisticGraphVertex v, LinguisticGraph* graph);

  QStringList getPredicate(LinguisticGraphVertex v);

  QString getMicro(LinguisticAnalysisStructure::MorphoSyntacticData* morphoData);

  QMultiMap<LinguisticGraphVertex, AnnotationGraphVertex> predicates;
  QString previousNeType;

  const FsaStringsPool* sp = nullptr;
  MediaId medId;
  std::shared_ptr< AbstractLinguisticProcessingClient > m_client;
  std::map<std::string,std::string> metaData;
  std::string splitMode;
  std::map<std::string, AbstractAnalysisHandler*> handlers;
  std::set<std::string> inactiveUnits;


  BowTextWriter* bowTextWriter = nullptr;
  EventAnalysis::EventHandler* eventHandler = nullptr;
  BowTextHandler* bowTextHandler = nullptr;
  SimpleStreamHandler* simpleStreamHandler = nullptr;
  SimpleStreamHandler* fullXmlSimpleStreamHandler = nullptr;
  LTRTextHandler* ltrTextHandler = nullptr;

  const Common::PropertyCode::PropertyAccessor* propertyAccessor = nullptr;
  LinguisticGraph* posGraph = nullptr;
  LinguisticGraph* anaGraph = nullptr;
  AnnotationData* annotationData = nullptr;
  const PropertyCodeManager* propertyCodeManager = nullptr;
  const PropertyManager* microManager = nullptr;
  const std::map< std::string, PropertyManager >* managers = nullptr;
  std::map< LinguisticGraphVertex,
          std::pair<LinguisticGraphVertex,
                    std::string> > vertexDependencyInformations;
  QMap<QString, QString> conllLimaDepMapping;

  std::set<std::string> dumpers = {"text"};

  std::map<LinguisticGraphVertex, int> vertexToToken;

  QString m_graph = "PosGraph";

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
  try
  {
    QStringList qlangs = QString::fromStdString(langs).split(",");
    QStringList qpipelines = QString::fromStdString(pipelines).split(",");
    m_d = new LimaAnalyzerPrivate(qlangs, qpipelines,
                                  QString::fromStdString(modulePath),
                                  QString::fromStdString(user_config_path),
                                  QString::fromStdString(user_resources_path),
                                  QString::fromStdString(meta));
  }
  catch (const Lima::LimaException& e)
  {
    std::cerr << "Lima internal error: " << e.what() << std::endl;
    m_d = nullptr;
    error = true;
    errorMessage = e.what();
  }
}

LimaAnalyzer::~LimaAnalyzer()
{
  delete m_d;
}

LimaAnalyzer::LimaAnalyzer(const LimaAnalyzer& a)
{
  try
  {
    m_d = new LimaAnalyzerPrivate(a.m_d->qlangs, a.m_d->qpipelines,
                                a.m_d->modulePath,
                                a.m_d->user_config_path,
                                a.m_d->user_resources_path,
                                a.m_d->meta);
  }
  catch (const Lima::LimaException& e)
  {
    std::cerr << "Lima internal error: " << e.what() << std::endl;
    m_d = nullptr;
    error = true;
    errorMessage = e.what();
  }
  // std::cerr << "LimaAnalyzer::LimaAnalyzer copy constructor" << std::endl;
}

LimaAnalyzer& LimaAnalyzer::operator=(const LimaAnalyzer& a)
{
  try
  {
    // std::cerr << "LimaAnalyzer::operator=" << std::endl;
    delete m_d;
    m_d = new LimaAnalyzerPrivate(a.m_d->qlangs, a.m_d->qpipelines,
                                  a.m_d->modulePath,
                                  a.m_d->user_config_path,
                                  a.m_d->user_resources_path,
                                  a.m_d->meta);
    return *this;
  }
  catch (const Lima::LimaException& e)
  {
    std::cerr << "Lima internal error: " << e.what() << std::endl;
    m_d = nullptr;
    error = true;
    errorMessage = e.what();
  }
}

Doc LimaAnalyzer::operator()(const std::string& text,
                                     const std::string& lang,
                                     const std::string& pipeline,
                                     const std::string& meta)
{
  try
  {
    return (*m_d)(text, lang, pipeline, meta);
  }
  catch (const Lima::LimaException& e)
  {
    std::cerr << "Lima internal error: " << e.what() << std::endl;
    error = true;
    errorMessage = e.what();
    auto doc = Doc(error, errorMessage);
    return doc;
  }
}

std::string LimaAnalyzer::analyzeText(const std::string& text,
                                    const std::string& lang,
                                    const std::string& pipeline,
                                    const std::string& meta)
{
//   std::cerr << "LimaAnalyzer::analyzeText" << std::endl;
  try
  {
    return m_d->analyzeText(text, lang, pipeline, meta);
  }
  catch (const Lima::LimaException& e)
  {
    std::cerr << "Lima internal error: " << e.what() << std::endl;
    error = true;
    errorMessage = e.what();
    return "";
  }
}

Doc LimaAnalyzerPrivate::operator()(
    const std::string& text,
    const std::string& lang,
    const std::string& pipeline,
    const std::string& meta)
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
    auto analysis = m_client->analyze(contentText, localMetaData, pipeline, handlers, inactiveUnits);
    return docFrom_analysis(analysis);
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
      m_client->analyze(contentText,
                      localMetaData,
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
      m_client->analyze(contentText, localMetaData, pipeline, handlers,
                        inactiveUnits);
    }
  }

  simpleStreamHandler->setOut(nullptr);
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

QString getFeats(const PropertyCodeManager& propertyCodeManager,
                 const LinguisticAnalysisStructure::MorphoSyntacticData& morphoData)
{
  auto managers = propertyCodeManager.getPropertyManagers();

  QStringList featuresList;
  for (auto i = managers.cbegin(); i != managers.cend(); i++)
  {
    auto key = QString::fromUtf8(i->first.c_str());
    if (key != "MACRO" && key != "MICRO")
    {
      const auto& pa = propertyCodeManager.getPropertyAccessor(key.toStdString());
      LinguisticCode lc = morphoData.firstValue(pa);
      auto value = QString::fromUtf8(i->second.getPropertySymbolicValue(lc).c_str());
      if (value != "NONE")
      {
        featuresList << QString("%1=%2").arg(key).arg(value);
      }
    }
  }

  featuresList.sort();
  QString features;
  QTextStream featuresStream(&features);
  if (featuresList.isEmpty())
  {
    features = "_";
  }
  else
  {
    for (auto featuresListIt = featuresList.cbegin(); featuresListIt != featuresList.cend(); featuresListIt++)
    {
      if (featuresListIt != featuresList.cbegin())
      {
        featuresStream << "|";
      }
      featuresStream << *featuresListIt;
    }
  }
#ifdef DEBUG_LP
  LDEBUG << "ConllDumper::process features:" << features;
#endif

  return features;
}

Doc LimaAnalyzerPrivate::docFrom_analysis(std::shared_ptr< Lima::AnalysisContent > analysis)
{
  // std::cerr << "docFrom_analysis" << std::endl;
  auto metadataholder = static_cast<LinguisticMetaData*>(analysis->getData("LinguisticMetaData"));
  const auto& lang = metadataholder->getMetaData("Lang");
  medId = MedData::single().media(lang);
  const auto& languageData = static_cast<const LanguageData&>(MedData::single().mediaData(medId));
  propertyCodeManager = &languageData.getPropertyCodeManager();
  propertyAccessor = &propertyCodeManager->getPropertyAccessor("MICRO");

  // std::cerr << "docFrom_analysis get stringsPool" << std::endl;
  Doc doc;
  doc.m_d->language = lang;
  sp = &MedData::single().stringsPool(MedData::single().media(lang));


  annotationData = static_cast<AnnotationData*>(analysis->getData("AnnotationData"));

  doc.m_d->analysis = analysis;
  auto anaGraphData = static_cast<LinguisticAnalysisStructure::AnalysisGraph*>(analysis->getData("AnalysisGraph"));
  anaGraph = anaGraphData->getGraph();
  auto posGraphData = static_cast<LinguisticAnalysisStructure::AnalysisGraph*>(analysis->getData("PosGraph"));
  if (posGraphData==0)
  {
    std::cerr << "Error: PosGraph has not been produced: check pipeline";
    return doc;
  }
  posGraph = posGraphData->getGraph();
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
  int sentenceNb = 0;
  LinguisticGraphVertex vEndDone = 0; // TODO remove. useless here. comes from LIMA ConllDumper
  std::map<LinguisticGraphVertex,int> segmentationMapping; // TODO remove. useless here. comes from LIMA ConllDumper
  std::map<int,LinguisticGraphVertex> segmentationMappingReverse; // TODO remove. useless here. comes from LIMA ConllDumper
  auto tokenId = 0;
  auto tokens = get(vertex_token, *posGraph);
  auto morphoDatas = get(vertex_data, *posGraph);
  // std::cerr << "docFrom_analysis before while" << std::endl;
  while (v != lastVertex)
  {
    // std::cerr << "docFrom_analysis on vertex " << v << posGraph << std::endl;

    dumpPosGraphVertex(doc, v,
                            tokenId,
                            vEndDone,
                            segmentationMapping,
                            "",
                            false);

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
  auto tmp = analysis->getData("SentenceBoundaries");
  if (tmp != 0)
  {
    auto sb = static_cast<SegmentationData*>(tmp);
    // if (sb->getGraphId() != "PosGraph") {
    //   LERROR << "SentenceBounds have been computed on " << sb->getGraphId() << " !";
    //   LERROR << "SyntacticAnalyzer-deps needs SentenceBounds on PosGraph";
    //   return INVALID_CONFIGURATION;
    // }
    for (auto bound: sb->getSegments())
    {
      auto sentenceBegin = bound.getFirstVertex();
      auto sentenceEnd = bound.getLastVertex();
      doc.m_d->sentences.push_back(Span(vertexToToken[sentenceBegin], vertexToToken[sentenceEnd]));

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
  }
  // std::cerr << "docFrom_analysis before return" << std::endl;
  return doc;
}


int LimaAnalyzerPrivate::dumpPosGraphVertex(
  Doc& doc,
  LinguisticGraphVertex v,
  int& tokenId,
  LinguisticGraphVertex vEndDone,
  std::map<LinguisticGraphVertex,int>& segmentationMapping,
  const QString& parentNeType,
  bool first)
{
  // std::cerr << "LimaAnalyzerPrivate::dumpPosGraphVertex IN " << v << std::endl;
#ifdef DEBUG_LP
  DUMPERLOGINIT;
  LDEBUG << "LimaAnalyzerPrivate::dumpPosGraphVertex IN" << v;
#endif
  if (anaGraph == nullptr || posGraph == nullptr || annotationData == nullptr)
  {
    DUMPERLOGINIT;
    LERROR << "LimaAnalyzerPrivate::dumpPosGraphVertex missing data";
    return MISSING_DATA;
  }
  bool notDone(true);
  if( v == vEndDone )
    notDone = false;

  auto ft = get(vertex_token, *posGraph, v);
  auto morphoData = get(vertex_data, *posGraph, v);
  if( morphoData != 0 && ft != 0
    && ((!morphoData->empty()) || ft->length() > 0) && notDone )
  {
#ifdef DEBUG_LP
    LDEBUG << "LimaAnalyzerPrivate::dumpPosGraphVertex PosGraph nb different LinguisticCode"
          << morphoData->size();
#endif
    // std::cerr << "LimaAnalyzerPrivate::dumpPosGraphVertex PosGraph nb different LinguisticCode"
    //       << morphoData->size() << std::endl;

    auto micro = getMicro(morphoData);
#ifdef DEBUG_LP
    LDEBUG << "LimaAnalyzerPrivate::dumpPosGraphVertex graphTag:" << micro;
#endif
    // std::cerr << "LimaAnalyzerPrivate::dumpPosGraphVertex graphTag:" << micro.toStdString() << std::endl;

    auto feats = getFeats(*propertyCodeManager, *morphoData);
#ifdef DEBUG_LP
    LDEBUG << "LimaAnalyzerPrivate::dumpPosGraphVertex feats:" << feats;
#endif
    // std::cerr << "LimaAnalyzerPrivate::dumpPosGraphVertex feats:" << feats.toStdString() << std::endl;

    auto inflectedToken = ft->stringForm().toStdString();
    // std::cerr << "LimaAnalyzerPrivate::dumpPosGraphVertex inflectedToken:" << inflectedToken << std::endl;
    if (inflectedToken.find_first_of("\r\n\t") != std::string::npos)
      boost::find_format_all(inflectedToken,
                              boost::token_finder(!boost::is_print()),
                              character_escaper());

    QString lemmatizedToken;
    if (morphoData != nullptr && !morphoData->empty())
    {
      lemmatizedToken = (*sp)[(*morphoData)[0].lemma];
    }
    // std::cerr << "LimaAnalyzerPrivate::dumpPosGraphVertex lemmatizedToken:" << lemmatizedToken << std::endl;
    // @TODO Should follow instructions here to output all MWE:
    // https://universaldependencies.org/format.html#words-tokens-and-empty-nodes
    QString neType = getNeType(v);
    QString neIOB = "O";
    // std::cerr << "LimaAnalyzerPrivate::dumpPosGraphVertex neType:" << neType << std::endl;
    // Collect NE vertices and output them instead of a single line for
    // current v. NE vertices can not only be PosGraph
    // vertices (and thus can just call dumpPosGraphVertex
    // recursively) but also AnalysisGraph vertices. In the latter case, data
    // come partly from the AnalysisGraph and partly from the PosGraph
    // Furthermore, named entities can be recursive...
    if (neType != "_")
    {
      dumpNamedEntity(doc, v, tokenId, vEndDone, segmentationMapping, neType);
    }
    else
    {
      if (!parentNeType.isEmpty())
      {
        neType = parentNeType;
      }

      // QString conllRelName;
      // QString targetConllIdString;
      // std::tie(conllRelName,
      //         targetConllIdString) = getConllRelName(v, segmentationMapping);
      //
      // QStringList miscField;
      if (neType != "_")
      {
#ifdef DEBUG_LP
      LDEBUG << "LimaAnalyzerPrivate::dumpPosGraphVertex specific entity type is"
              << neType;
#endif
        neIOB = first?"B":"I";
        // const auto annot = getSpecificEntityAnnotation(v);
// #ifdef DEBUG_LP
//         LDEBUG << "LimaAnalyzerPrivate::dumpPosGraphVertex specific entity annotation is"
//                 << annot;
// #endif
        // TODO Add entity features to python API
        // if (annot != nullptr)
        // {
        //   const auto& features = annot->getFeatures();
        //   for (const auto& feature: features)
        //   {
        //     QString featureString;
        //     QTextStream qts(&featureString);
        //     if(feature.getPosition() == UNDEFPOSITION
        //        && !feature.getName().empty()
        //        && !feature.getValueString().empty())
        //     {
        //       qts << "NE-" << QString::fromStdString(feature.getName()) << "=";
        //       qts << Common::Misc::transcodeToXmlEntities(
        //         QString::fromStdString(feature.getValueString()));
        //     }
        //     miscField << featureString;
        //   }
        // }
      }


      // if(!hasSpaceAfter(v, posGraph)) // TODO use hasSpaceAfter in Token
      auto features = getFeats(*propertyCodeManager, *morphoData);

      // std::cerr << "docFrom_analysis token/lemma are " << inflectedToken << "/" << lemmatizedToken << std::endl;

      auto pos = ft->position();
      auto len = ft->length();
      auto tStatus = ft->status().defaultKey();

      Token t(len, inflectedToken, lemmatizedToken.toStdString(),
              tokenId++, pos, micro.toStdString(), 0, "", features.toStdString(),
              neIOB.toStdString(), neType.toStdString(), tStatus.toStdString());
      vertexToToken[v] = tokenId;
      // std::cerr << "docFrom_analysis pushing token" << std::endl;
      doc.m_d->tokens.push_back(t);
      previousNeType = neType;
    }
  }
  return SUCCESS_ID;
}

void LimaAnalyzerPrivate::dumpNamedEntity(Doc& doc,
                                         LinguisticGraphVertex v,
                                         int& tokenId,
                                         LinguisticGraphVertex vEndDone,
                                         std::map<LinguisticGraphVertex,int>& segmentationMapping,
                                         const QString& neType)
{
  std::cerr << "LimaAnalyzerPrivate::dumpNamedEntity IN" << v << std::endl;
#ifdef DEBUG_LP
  DUMPERLOGINIT;
  LDEBUG << "LimaAnalyzerPrivate::dumpNamedEntity" << v << tokenId << vEndDone
          << neType;
#endif
  // Check if the named entity is on AnalysisGraph.
  // If so, then we have to recursively get all analysis graph tokens and
  // collect the information about them, chosing randomly the "right" category
  // Otherwise, will retrieve the pos graph tokens and recursively do the same.
  // For final tokens that are on pos graph, the category will be unique.

  if (annotationData != nullptr)
  {
    // Check if the PosGraph vertex holds a specific entity
    auto matches = annotationData->matches(m_graph.toStdString(), v, "annot");
#ifdef DEBUG_LP
    LDEBUG << "LimaAnalyzerPrivate::dumpNamedEntity matches PosGraph" << v
            << "annot:" << matchesS(matches);
#endif
    for (const auto& vx: matches)
    {
      if (annotationData->hasAnnotation(vx, QString::fromUtf8("SpecificEntity")))
      {
        auto se = annotationData->annotation(vx, QString::fromUtf8("SpecificEntity"))
          .pointerValue<SpecificEntityAnnotation>();
        previousNeType = "O";
        bool first = true;
        for (const auto& vse : se->vertices())
        {
          dumpPosGraphVertex(doc, vse, tokenId, vEndDone, segmentationMapping, neType, first);
          first = false;
        }
#ifdef DEBUG_LP
        LDEBUG << "LimaAnalyzerPrivate::dumpNamedEntity return after SpecificEntity annotation on PosGraph";
#endif
        return;
      }
    }
    auto anaVertices = annotationData->matches(m_graph.toStdString(), v, "AnalysisGraph");
#ifdef DEBUG_LP
    LDEBUG << "LimaAnalyzerPrivate::dumpNamedEntity anaVertices for" << v << ":" << matchesS(anaVertices);
#endif

    assert(anaVertices.size() == 1);
    auto anaVertex = *anaVertices.begin();
#ifdef DEBUG_LP
    LDEBUG << "LimaAnalyzerPrivate::dumpNamedEntity anaVertex is" << anaVertex;
#endif
    if (annotationData->hasAnnotation(anaVertex, QString::fromUtf8("SpecificEntity")))
    {
      auto se = annotationData->annotation(anaVertex, QString::fromUtf8("SpecificEntity"))
        .pointerValue<SpecificEntityAnnotation>();
#ifdef DEBUG_LP
      LDEBUG << "LimaAnalyzerPrivate::dumpNamedEntity anaVertex se ("
              << (*sp)[se->getString()]
              << ") annotation vertices are" << se->vertices()
              << "and normalized form:" << (*sp)[se->getNormalizedForm()]
               << "and features:" << se->getFeatures();
#endif
      // All retrieved lines/tokens have the same netype. Depending on the
      // output style (CoNLL 2003, CoNLL-U, …), the generated line is different
      // and the ne-Type includes or not BIO information using in this case the
      // previousNeType member.
      previousNeType = "O";
      bool first = true;
      for (const auto& vse : se->vertices())
      {
        dumpAnalysisGraphVertex(doc, vse, v, tokenId, vEndDone, neType, first, se->getFeatures());
        first = false;
      }
      previousNeType = neType;
    }
  }
}

// TODO Split idiomatic alternative tokens and compound tokens
int LimaAnalyzerPrivate::dumpAnalysisGraphVertex(
  Doc& doc,
  LinguisticGraphVertex v,
  LinguisticGraphVertex posGraphVertex,
  int& tokenId,
  LinguisticGraphVertex vEndDone,
  const QString& neType,
  bool first,
  const Automaton::EntityFeatures& features)
{
  // std::cerr << "LimaAnalyzerPrivate::dumpAnalysisGraphVertex" << v << posGraphVertex << neType << std::endl;
  LIMA_UNUSED(posGraphVertex);
#ifdef DEBUG_LP
  DUMPERLOGINIT;
  LDEBUG << "LimaAnalyzerPrivate::dumpAnalysisGraphVertex" << v << posGraphVertex << neType;
#endif
  if (anaGraph == nullptr || posGraph == nullptr || annotationData == nullptr)
  {
    DUMPERLOGINIT;
    LERROR << "LimaAnalyzerPrivate::dumpAnalysisGraphVertex missing data";
    return MISSING_DATA;
  }
  bool notDone(true);
  if( v == vEndDone )
    notDone = false;

  auto ft = get(vertex_token, *anaGraph, v);
  auto morphoData = get(vertex_data, *anaGraph, v);
#ifdef DEBUG_LP
  LDEBUG << "LimaAnalyzerPrivate::dumpAnalysisGraphVertex PosGraph token" << v;
#endif
  if( morphoData != nullptr && ft != nullptr && ((!morphoData->empty()) || ft->length() > 0) && notDone )
  {
#ifdef DEBUG_LP
    LDEBUG << "LimaAnalyzerPrivate::dumpAnalysisGraphVertex PosGraph nb different LinguisticCode"
          << morphoData->size();
#endif

    auto micro = getMicro(morphoData);
#ifdef DEBUG_LP
    LDEBUG << "LimaAnalyzerPrivate::dumpAnalysisGraphVertex micro:" << micro;
#endif

    auto feats = getFeats(*propertyCodeManager, *morphoData);
#ifdef DEBUG_LP
    LDEBUG << "LimaAnalyzerPrivate::dumpAnalysisGraphVertex feats:" << feats;
#endif

    auto inflectedToken = ft->stringForm().toStdString();
    if (inflectedToken.find_first_of("\r\n\t") != std::string::npos)
      boost::find_format_all(inflectedToken,
                             boost::token_finder(!boost::is_print()),
                             character_escaper());

    QString lemmatizedToken;
    if (morphoData != 0 && !morphoData->empty())
    {
      lemmatizedToken = (*sp)[(*morphoData)[0].lemma];
    }
    // @TODO Should follow instructions here to output all MWE:
    // https://universaldependencies.org/format.html#words-tokens-and-empty-nodes

    // TODO Get correct UD dep relation for relations inside the named entity
    // and for the token that must be linked to the outside. For this one, the
    // relation is the one which links to posGraphVertex to the rest of the pos
    // graph.
    QString conllRelName = "_";
    QString targetConllIdString = "_";
    QString neIOB = first?"B-":"I-";
//     QStringList miscField;
//     if (neType != "_")
//     {
// #ifdef DEBUG_LP
//       LDEBUG << "LimaAnalyzerPrivate::dumpAnalysisGraphVertex specific entity type is" << neType;
//       LDEBUG << "LimaAnalyzerPrivate::dumpAnalysisGraphVertex posGraphVertex is" << posGraphVertex;
// #endif
//       miscField << (QString("NE=") + (first?"B-":"I-") + neType);
//       for (const auto& feature: features)
//       {
//         if(!feature.getName().empty()
//            && !feature.getValueString().empty())
//         {
//           QString featureString;
//           QTextStream qts(&featureString);
//           qts << "NE-" << QString::fromStdString(feature.getName()) << "=";
//           qts << Common::Misc::transcodeToXmlEntities(
//             QString::fromStdString(feature.getValueString()));
//           miscField << featureString;
//         }
//       }
//     }

    // miscField << (QString("Pos=") + QString::number(ft->position()) );
    // miscField << (QString("Len=") +  QString::number(ft->length()) );
    //
    // if(!hasSpaceAfter(v, anaGraph))
    // {
    //   miscField << QString("SpaceAfter=No");
    // }
    //
    // miscField << getPredicate(v);
    //
    // if (miscField.empty())
    // {
    //   miscField << "_";
    // }
    auto pos = ft->position();
    auto len = ft->length();
    auto tStatus = ft->status().defaultKey();
    auto features = getFeats(*propertyCodeManager, *morphoData);
    Token t(len, inflectedToken, lemmatizedToken.toStdString(), tokenId++, pos,
            micro.toStdString(), 0, "", features.toStdString(),
            neIOB.toStdString(), neType.toStdString(), tStatus.toStdString());
    vertexToToken[v] = tokenId;
    // std::cerr << "docFrom_analysis pushing token" << std::endl;
    doc.m_d->tokens.push_back(t);
  }
  return SUCCESS_ID;
}

QString LimaAnalyzerPrivate::getNeType(LinguisticGraphVertex posGraphVertex)
{
  // std::cerr << "LimaAnalyzerPrivate::getNeType "<< posGraphVertex << std::endl;
  auto neType = QString::fromUtf8("_") ;
  if (annotationData != nullptr)
  {
    // Check if the PosGraph vertex holds a specific entity
    // std::cerr << "LimaAnalyzerPrivate::getNeType call matches with " << m_graph.toStdString()
    //     << " and " << posGraphVertex << std::endl;
    auto matches = annotationData->matches(m_graph.toStdString(), posGraphVertex, "annot");
    // std::cerr << "LimaAnalyzerPrivate::getNeType got" << matches.size() << " matches" << std::endl;
    for (const auto& vx: matches)
    {
      // std::cerr << "LimaAnalyzerPrivate::getNeType on match " << vx << std::endl;
      if (annotationData->hasAnnotation(vx, QString::fromUtf8("SpecificEntity")))
      {
        auto se = annotationData->annotation(vx, QString::fromUtf8("SpecificEntity")).
          pointerValue<SpecificEntityAnnotation>();
        neType = MedData::single().getEntityName(se->getType());
        break;
      }
    }
    if (neType == "_")
    {
      // The PosGraph vertex did not hold a specific entity,
      // check if the AnalysisGraph vertex does
      // std::cerr << "LimaAnalyzerPrivate::getNeType checking AnalysisGraph" << std::endl;
      auto anaVertices = annotationData->matches(m_graph.toStdString(), posGraphVertex, "AnalysisGraph");
      // note: anaVertices size should be 0 or 1
      for (const auto& anaVertex: anaVertices)
      {
        // std::cerr << "LimaAnalyzerPrivate::getNeType on AnalysisGraph vertex " << anaVertex << std::endl;
        auto matches = annotationData->matches("AnalysisGraph", anaVertex, "annot");
        for (const auto& vx: matches)
        {
          // std::cerr << "LimaAnalyzerPrivate::getNeType on ana match " << vx << std::endl;
          if (annotationData->hasAnnotation(vx, QString::fromUtf8("SpecificEntity")))
          {
            auto se = annotationData->annotation(vx, QString::fromUtf8("SpecificEntity"))
                .pointerValue<SpecificEntityAnnotation>();
            neType = MedData::single().getEntityName(se->getType());
            break;
          }
        }
        if (neType != "_") break;
      }
    }
  }
  // std::cerr << "LimaAnalyzerPrivate::getNeType for " << posGraphVertex << ". result = " << neType << std::endl;
  return neType;
}

// std::pair<QString, QString> LimaAnalyzerPrivate::getConllRelName(
//   LinguisticGraphVertex v,
//   std::map<LinguisticGraphVertex,int>& segmentationMapping)
// {
// #ifdef DEBUG_LP
//   DUMPERLOGINIT;
//   LDEBUG << "LimaAnalyzerPrivate::getConllRelName" << v;
// #endif
//   QString conllRelName = "_";
//   int targetConllId = 0;
//   if (vertexDependencyInformations.count(v) != 0)
//   {
//     auto target = vertexDependencyInformations.find(v)->second.first;
// #ifdef DEBUG_LP
//     LDEBUG << "ConllDumper::process target saved for"
//             << v << "is" << target;
// #endif
//     if (segmentationMapping.find(target) != segmentationMapping.end())
//     {
//       targetConllId =  segmentationMapping.find(target)->second;
//     }
//     else
//     {
//       DUMPERLOGINIT;
//       LERROR << "ConllDumper::process target" << target
//               << "not found in segmentation mapping";
//     }
// #ifdef DEBUG_LP
//     LDEBUG << "ConllDumper::process conll target saved for "
//             << v << " is " << targetConllId;
// #endif
//     auto relName = QString::fromUtf8(
//       vertexDependencyInformations.find(v)->second.second.c_str());
// #ifdef DEBUG_LP
//     LDEBUG << "ConllDumper::process the lima dependency tag for "
//             << v << " is " << relName;
// #endif
//     if (conllLimaDepMapping.contains(relName))
//     {
//       conllRelName = conllLimaDepMapping[relName];
//     }
//     else
//     {
//       conllRelName = relName;
// //             LERROR << "ConllDumper::process" << relName << "not found in mapping";
//     }
//
//     // There is no way for vertex to have 0 as head.
//     if (conllRelName == "root")
//     {
//       targetConllId = 0;
//     }
//   }
//   QString targetConllIdString = QString(QLatin1String("%1")).arg(targetConllId);
//
//   return { conllRelName, targetConllIdString };
// }

const SpecificEntityAnnotation* LimaAnalyzerPrivate::getSpecificEntityAnnotation(
  LinguisticGraphVertex v) const
{
  // check only entity found in current graph (not previous graph such as AnalysisGraph)

  for (const auto& vx: annotationData->matches("PosGraph", v, "annot"))
  {
    if (annotationData->hasAnnotation(vx, QString::fromUtf8("SpecificEntity")))
    {
      //BoWToken* se = createSpecificEntity(v,*it, annotationData, anagraph, posgraph, offsetBegin);
      auto se = annotationData->annotation(
        vx,
        QString::fromUtf8("SpecificEntity")).pointerValue<SpecificEntityAnnotation>();
      if (se != nullptr)
      {
        return se;
      }
    }
  }
  return nullptr;

}

bool LimaAnalyzerPrivate::hasSpaceAfter(LinguisticGraphVertex v, LinguisticGraph* graph)
{
  auto ft = get(vertex_token, *graph, v);
  bool SpaceAfter = true;
  LinguisticGraphOutEdgeIt outIter, outIterEnd;
  for (auto [outIter, outIterEnd] = boost::out_edges(v, *graph);
        outIter != outIterEnd; outIter++)
  {
      auto next = boost::target(*outIter, *graph);
      auto nt = get(vertex_token, *graph, next);
      if( nt != nullptr && (nt->position() == ft->position()+ft->length()) )
      {
          SpaceAfter = false;
          break;
      }
  }
  return SpaceAfter;
}

QStringList LimaAnalyzerPrivate::getPredicate(LinguisticGraphVertex v)
{
#ifdef DEBUG_LP
  DUMPERLOGINIT;
  LDEBUG << "LimaAnalyzerPrivate::getPredicate" << v;
#endif

  QStringList miscField;
  if (annotationData != nullptr && predicates.contains(v))
  {
    auto keys = predicates.keys();
    auto predicate = annotationData->stringAnnotation(predicates.value(v),
                                                      "Predicate");

    // Now output the roles supported by the current PoS graph token
#ifdef DEBUG_LP
    LDEBUG << "ConllDumper::process output the roles for the"
            << keys.size() << "predicates";
#endif
    for (int i = 0; i < keys.size(); i++)
    {
      auto predicateVertex = predicates.value(keys[keys.size()-1-i]);

      auto vMatches = annotationData->matches(m_graph.toStdString(), v, "annot");
      if (!vMatches.empty())
      {
#ifdef DEBUG_LP
        LDEBUG << "ConllDumper::process there is" << vMatches.size()
                << "nodes matching PoS graph vertex" << v
                << "in the annotation graph.";
#endif
        QString roleAnnotation;
        for (auto it = vMatches.begin(); it != vMatches.end(); it++)
        {
          auto vMatch = *it;
          AnnotationGraphInEdgeIt vMatchInEdgesIt, vMatchInEdgesIt_end;
          boost::tie(vMatchInEdgesIt, vMatchInEdgesIt_end) =
              boost::in_edges(vMatch,annotationData->getGraph());
          for (; vMatchInEdgesIt != vMatchInEdgesIt_end; vMatchInEdgesIt++)
          {
            auto inVertex = boost::source(*vMatchInEdgesIt,
                                          annotationData->getGraph());
            auto inVertexAnnotPosGraphMatches = annotationData->matches(
              "annot",inVertex,m_graph.toStdString());
            if (inVertex == predicateVertex
                && !inVertexAnnotPosGraphMatches.empty())
            {
              // Current edge is holding a role of the current predicate
              roleAnnotation =
                  annotationData->stringAnnotation(*vMatchInEdgesIt,
                                                    "SemanticRole");
              break;
            }
          }
        }
        if (!roleAnnotation.isEmpty() )
          predicate = roleAnnotation + ":" + predicate;
      }
    }
    if (!predicate.isEmpty())
    {
      miscField << predicate;
    }
  }
  return miscField;
}

QString LimaAnalyzerPrivate::getMicro(LinguisticAnalysisStructure::MorphoSyntacticData* morphoData)
{
  return QString::fromUtf8(static_cast<const LangData&>(
      MedData::single().mediaData(medId)).getPropertyCodeManager()
        .getPropertyManager("MICRO")
        .getPropertySymbolicValue(morphoData->firstValue(
          *propertyAccessor)).c_str());
}

