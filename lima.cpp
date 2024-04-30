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
#include <linguisticProcessing/core/LinguisticAnalysisStructure/AnalysisGraph.h>
#include "linguisticProcessing/core/LinguisticAnalysisStructure/MorphoSyntacticData.h"
#include "linguisticProcessing/core/LinguisticProcessors/LinguisticMetaData.h"
#include "linguisticProcessing/core/LinguisticResources/AbstractResource.h"
#include "linguisticProcessing/core/LinguisticResources/LinguisticResources.h"
#include "linguisticProcessing/core/SyntacticAnalysis/DependencyGraph.h"
#include "linguisticProcessing/core/SyntacticAnalysis/SyntacticData.h"
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

#define DEBUG_LP

using namespace Lima::LinguisticProcessing;
using namespace Lima::LinguisticProcessing::SpecificEntities;
using namespace Lima::LinguisticProcessing::SyntacticAnalysis;
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

  void collectDependencyInformations(std::shared_ptr<Lima::AnalysisContent> analysis);
  void collectVertexDependencyInformations(LinguisticGraphVertex v,
                                           std::shared_ptr<Lima::AnalysisContent> analysis);

  Doc docFrom_analysis(std::shared_ptr<Lima::AnalysisContent> analysis);

  int dumpPosGraphVertex(Doc& doc,
                         LinguisticGraphVertex v,
                         int& tokenId,
                         LinguisticGraphVertex vEndDone,
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
                       const QString& neType);

  /** Gets the named entity type for the PosGraph vertex @ref posGraphVertex
   * if it is a specific entity. Return "_" otherwise
   */
  QString getNeType(LinguisticGraphVertex posGraphVertex);

  std::pair<QString, int> getConllRelName(LinguisticGraphVertex v);

  const SpecificEntityAnnotation* getSpecificEntityAnnotation(LinguisticGraphVertex v) const;

  bool hasSpaceAfter(LinguisticGraphVertex v, LinguisticGraph* graph);

  QString getMicro(LinguisticAnalysisStructure::MorphoSyntacticData& morphoData);

  QString getFeats(const LinguisticAnalysisStructure::MorphoSyntacticData& morphoData);

  /** Reset all members used to store analysis states. To be called before handling a new analysis. */
  void reset();

  std::map<std::string, std::string> parseMetaData(const QString& meta,
                                                   QChar comma = ',',
                                                   QChar colon = ':',
                                                   const std::map<std::string, std::string>& append = {});

  QString previousNeType;

  const FsaStringsPool* sp = nullptr;
  MediaId medId;


  const LanguageData* languageData = nullptr;
  const Common::PropertyCode::PropertyAccessor* propertyAccessor = nullptr;
  LinguisticGraph* posGraph = nullptr;
  LinguisticGraph* anaGraph = nullptr;
  std::shared_ptr<AnnotationData> annotationData = nullptr;
  std::shared_ptr<SyntacticData> syntacticData = nullptr;
  std::map< LinguisticGraphVertex,
          std::pair<LinguisticGraphVertex,
                    std::string> > vertexDependencyInformations;
  QMap<QString, QString> conllLimaDepMapping;


  std::map<LinguisticGraphVertex, int> vertexToToken;

  const PropertyCodeManager* propertyCodeManager = nullptr;
  // Fixed members that do not change at each analysis
  std::map<std::string, AbstractAnalysisHandler*> handlers;
  std::unique_ptr<BowTextWriter> bowTextWriter = nullptr;
  std::unique_ptr<BowTextHandler> bowTextHandler = nullptr;
  std::unique_ptr<SimpleStreamHandler> simpleStreamHandler = nullptr;
  std::unique_ptr<SimpleStreamHandler> fullXmlSimpleStreamHandler = nullptr;
  std::unique_ptr<LTRTextHandler> ltrTextHandler = nullptr;
  std::set<std::string> dumpers = {"text"};
  std::shared_ptr< AbstractLinguisticProcessingClient > m_client;
  std::map<std::string,std::string> metaData;
  // Store constructor parameters to be able to implement copy constructor
  QStringList qlangs;
  QStringList qpipelines;
  QString modulePath;
  QString user_config_path;
  QString user_resources_path;
  QString meta;

  bool error = false;
  std::string errorMessage = "";

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

  if(iqlangs.size() == 0)
  {
    throw LimaException("Must initialize at least one language");
  }
  if(iqpipelines.size() == 0)
  {
    throw LimaException("Must initialize at least one pipeline");
  }


  QStringList additionalPaths({modulePath+"/config"});
  // Add here LIMA_CONF content in front, otherwise it will be ignored
  auto limaConf = QString::fromUtf8(qgetenv("LIMA_CONF").constData());
  if (!limaConf.isEmpty())
    additionalPaths = limaConf.split(LIMA_PATH_SEPARATOR,
                                     Qt::SkipEmptyParts) + additionalPaths;
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
    additionalResourcePaths = limaRes.split(LIMA_PATH_SEPARATOR, Qt::SkipEmptyParts) + additionalResourcePaths;
  if (!user_resources_path.isEmpty())
    additionalResourcePaths.push_front(user_resources_path);
  auto resourcesDirs = buildResourcesDirectoriesList(QStringList({"lima"}),
                                                     additionalResourcePaths);
  auto resourcesPath = resourcesDirs.join(LIMA_PATH_SEPARATOR);

  QsLogging::initQsLog(configPath);
  std::cerr << "QsLog initialized" << std::endl;
  // Necessary to initialize factories
  Lima::AmosePluginsManager::single();
  std::cerr << "LimaAnalyzerPrivate::LimaAnalyzerPrivate() plugins manager created" << std::endl;
  if (!Lima::AmosePluginsManager::changeable().loadPlugins(configPath))
  {
    throw InvalidConfiguration("loadLibrary method failed.");
  }
  std::cerr << "Amose plugins are now initialized hop" << std::endl;
  qDebug() << "Amose plugins are now initialized";


  std::string lpConfigFile = "lima-analysis.xml";
  std::string commonConfigFile = "lima-common.xml";
  std::string clientId = "lima-coreclient";

  std::string strConfigPath;

  // parse 'meta' argument to add metadata
  metaData = parseMetaData(meta, ',', ':', metaData);

  std::deque<std::string> pipelines;
  for (const auto& pipeline: qpipelines)
    pipelines.push_back(pipeline.toStdString());


  uint64_t beginTime=TimeUtils::getCurrentTime();

  std::deque<std::string> langs;
  for (const auto& lang: qlangs)
    langs.push_back(lang.toStdString());
  std::cerr << "LimaAnalyzerPrivate::LimaAnalyzerPrivate() NEW VERSION !"
            << resourcesPath.toUtf8().constData() << ", "
            << configPath.toUtf8().constData() << ", "
            << commonConfigFile << ", "
            << langs.front() << std::endl;
  std::cerr << "metadata:" << std::endl;
  for (const auto& elem: metaData)
  {
    std::cerr << "\t" << elem.first << " : " << elem.second << std::endl;
  }
  // initialize common
  Common::MediaticData::MediaticData::changeable().init(
    resourcesPath.toUtf8().constData(),
    configPath.toUtf8().constData(),
    commonConfigFile,
    langs,
    metaData);
  std::cerr << "MediaticData initialized" << std::endl;

  bool clientFactoryConfigured = false;
  Q_FOREACH(QString configDir, configDirs)
  {
    if (QFileInfo::exists(configDir + "/" + lpConfigFile.c_str()))
    {
      std::cerr << "LimaAnalyzerPrivate::LimaAnalyzerPrivate() configuring "
          << (configDir + "/" + lpConfigFile.c_str()).toUtf8().constData() << ", "
          << clientId << std::endl;

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
  std::cerr << "Client factory configured" << std::endl;

  m_client = std::dynamic_pointer_cast<AbstractLinguisticProcessingClient>(
    LinguisticProcessingClientFactory::single().createClient(clientId));

  // Set the handlers
  bowTextWriter = std::make_unique<BowTextWriter>();
  handlers.insert(std::make_pair("bowTextWriter", bowTextWriter.get()));
  bowTextHandler = std::make_unique<BowTextHandler>();
  handlers.insert(std::make_pair("bowTextHandler", bowTextHandler.get()));
  simpleStreamHandler = std::make_unique<SimpleStreamHandler>();
  handlers.insert(std::make_pair("simpleStreamHandler", simpleStreamHandler.get()));
  fullXmlSimpleStreamHandler = std::make_unique<SimpleStreamHandler>();
  handlers.insert(std::make_pair("fullXmlSimpleStreamHandler", fullXmlSimpleStreamHandler.get()));
  ltrTextHandler= std::make_unique<LTRTextHandler>();
  handlers.insert(std::make_pair("ltrTextHandler", ltrTextHandler.get()));
  std::cerr << "LimaAnalyzerPrivate constructor done" << std::endl;

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
    QStringList qlangs = QString::fromStdString(langs).split(",",
                                                             Qt::SkipEmptyParts);
    QStringList qpipelines = QString::fromStdString(pipelines).split(
      ",", Qt::SkipEmptyParts);
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
  }
  return *this;
}

/** return true if an error occured */
bool LimaAnalyzer::error()
{
  return m_d == nullptr || m_d->error;
}
/** return the error message if an error occured and reset the error state */
std::string LimaAnalyzer::errorMessage()
{
  if (m_d == nullptr)
  {
    return "Error during constructor";
  }
  std::string result = m_d->errorMessage;
  m_d->reset();
  return result;
}


void LimaAnalyzerPrivate::reset()
{
  previousNeType = "O";
  sp = nullptr;
  medId = 0;
  languageData = nullptr;
  syntacticData = nullptr;
  propertyAccessor = nullptr;
  posGraph = nullptr;
  anaGraph = nullptr;
  annotationData = nullptr;
  propertyCodeManager = nullptr;
  vertexDependencyInformations.clear();
  conllLimaDepMapping.clear();
  vertexToToken.clear();
  error = false;
  errorMessage = "";
}

Doc LimaAnalyzer::operator()(const std::string& text,
                                     const std::string& lang,
                                     const std::string& pipeline,
                                     const std::string& meta)
{
  if (m_d == nullptr)
  {
    auto doc = Doc(true, "No analyzer available");
    return doc;
  }
  else if (m_d->error)
  {
    m_d->error = true;
    m_d->errorMessage = "Invalid Lima analyzer. Previous error message was: " + m_d->errorMessage;
    auto doc = Doc(true, m_d->errorMessage);
    return doc;
  }
  try
  {
    return (*m_d)(text, lang, pipeline, meta);
  }
  catch (const Lima::LimaException& e)
  {
    std::cerr << "Lima internal error: " << e.what() << std::endl;
    m_d->error = true;
    m_d->errorMessage = e.what();
    auto doc = Doc(m_d->error, m_d->errorMessage);
    return doc;
  }
}

std::string LimaAnalyzer::analyzeText(const std::string& text,
                                    const std::string& lang,
                                    const std::string& pipeline,
                                    const std::string& meta)
{
  std::cerr << "LimaAnalyzer::analyzeText" << std::endl;
  if (m_d == nullptr)
  {
    return "";
  }
  else if (m_d->error)
  {
    m_d->errorMessage = "Invalid Lima analyzer. Previous error message was: " + m_d->errorMessage;
    return "";
  }
  try
  {
    return m_d->analyzeText(text, lang, pipeline, meta);
  }
  catch (const Lima::LimaException& e)
  {
    std::cerr << "Lima internal error: " << e.what() << std::endl;
    m_d->error = true;
    m_d->errorMessage = e.what();
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
  auto qmeta = QString::fromStdString(meta).split(",", Qt::SkipEmptyParts);
  for (const auto& m: qmeta)
  {
    auto kv = m.split(":", Qt::SkipEmptyParts);
    if (kv.size() == 2)
      localMetaData[kv[0].toStdString()] = kv[1].toStdString();
  }

  auto localLang = lang;
  if (localLang.size() == 0)
  {
    localLang = qlangs[0].toStdString();
  }
  auto localPipeline = pipeline;
  if (localPipeline.size() == 0)
  {
    localPipeline = qpipelines[0].toStdString();
  }
  localMetaData["Lang"] = localLang;

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
    auto analysis = m_client->analyze(contentText, localMetaData, localPipeline, handlers);
    return docFrom_analysis(analysis);
  }
}

const std::string LimaAnalyzerPrivate::analyzeText(const std::string& text,
                                    const std::string& lang,
                                    const std::string& pipeline,
                                    const std::string& meta)
{
  auto txtofs  = openHandlerOutputString(simpleStreamHandler.get(), dumpers, "text");

  auto localMetaData = parseMetaData(QString::fromStdString(meta), ',', ':', metaData);
  localMetaData["FileName"]="param";
  auto qmeta = QString::fromStdString(meta).split(",", Qt::SkipEmptyParts);
  for (const auto& m: qmeta)
  {
    auto kv = m.split(":", Qt::SkipEmptyParts);
    if (kv.size() == 2)
      localMetaData[kv[0].toStdString()] = kv[1].toStdString();
  }

  auto localLang = lang;
  if (localLang.size() == 0)
  {
    localLang = qlangs[0].toStdString();
  }
  auto localPipeline = pipeline;
  if (localPipeline.size() == 0)
  {
    localPipeline = qpipelines[0].toStdString();
  }
  localMetaData["Lang"] = localLang;

  QString contentText = QString::fromUtf8(text.c_str());
  if (contentText.isEmpty())
  {
    std::cerr << "Empty input ! " << std::endl;
  }
  else
  {
    // analyze it
    std::cerr << "Analyzing " << contentText.toStdString() << std::endl;
    m_client->analyze(contentText, localMetaData, localPipeline, handlers);
  }
  auto result = txtofs->str();
  std::cerr << "LimaAnalyzerPrivate::analyzeText result: " << result << std::endl;
  simpleStreamHandler->setOut(nullptr);
  return result;
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
  else
  {
    DUMPERLOGINIT;
    LERROR << dumperId << "is not in the dumpers list";
  }
  return ofs;
}

QString LimaAnalyzerPrivate::getFeats(const LinguisticAnalysisStructure::MorphoSyntacticData& morphoData)
{
#ifdef DEBUG_LP
  DUMPERLOGINIT;
  LDEBUG << "getFeats";
#endif
  auto managers = propertyCodeManager->getPropertyManagers();

  QStringList featuresList;
  for (auto i = managers.cbegin(); i != managers.cend(); i++)
  {
    auto key = QString::fromUtf8(i->first.c_str());
    if (key != "MACRO" && key != "MICRO")
    {
      const auto& pa = propertyCodeManager->getPropertyAccessor(key.toStdString());
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
  LDEBUG << "LimaAnalyzerPrivate::getFeats features:" << features;
#endif

  return features;
}

void LimaAnalyzerPrivate::collectDependencyInformations(std::shared_ptr<Lima::AnalysisContent> analysis)
{
#ifdef DEBUG_LP
  DUMPERLOGINIT;
  LDEBUG << "LimaAnalyzerPrivate::collectVertexDependencyInformations";
#endif

  auto posGraphData = std::dynamic_pointer_cast<LinguisticAnalysisStructure::AnalysisGraph>(analysis->getData("PosGraph"));
  if (posGraphData == nullptr)
  {
    std::cerr << "Error: PosGraph has not been produced: check pipeline";
    return;
  }

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

  syntacticData = std::dynamic_pointer_cast<SyntacticData>(analysis->getData("SyntacticData"));
  if (syntacticData == nullptr)
  {
    syntacticData = std::make_shared<SyntacticData>(posGraphData.get(), nullptr);
    syntacticData->setupDependencyGraph();
    analysis->setData("SyntacticData", syntacticData.get());
  }
  int tokenId = 0;

  while (v != lastVertex)
  {
    QString neType = getNeType(v);
    QString neIOB = "O";
    // Collect NE vertices and output them instead of a single line for
    // current v. NE vertices can not only be PosGraph
    // vertices (and thus can just call dumpPosGraphVertex
    // recursively) but also AnalysisGraph vertices. In the latter case, data
    // come partly from the AnalysisGraph and partly from the PosGraph
    // Furthermore, named entities can be recursive...
    if (neType != "_")
    {
      auto matches = annotationData->matches("PosGraph", v, "annot");
      if (!matches.empty())
      {
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
              collectVertexDependencyInformations(vse, analysis);
              vertexToToken[vse] = tokenId;
              first = false;
            }
            break;
          }
        }
      }
      else
      {
        auto anaVertices = annotationData->matches("PosGraph", v, "AnalysisGraph");
        auto anaVertex = *anaVertices.begin();
        if (annotationData->hasAnnotation(anaVertex, QString::fromUtf8("SpecificEntity")))
        {
          auto se = annotationData->annotation(anaVertex, QString::fromUtf8("SpecificEntity"))
            .pointerValue<SpecificEntityAnnotation>();
          // All retrieved lines/tokens have the same netype. Depending on the
          // output style (CoNLL 2003, CoNLL-U, …), the generated line is different
          // and the ne-Type includes or not BIO information using in this case the
          // previousNeType member.
          previousNeType = "O";
          bool first = true;
          vertexToToken[v] = tokenId;
          tokenId++;
          for (const auto& vse : se->vertices())
          {
            auto posVertices = annotationData->matches("AnalysisGraph", vse, "PosGraph");
            auto posVertex = *posVertices.begin();
            // @TODO Should follow instructions here to output all MWE:
            // https://universaldependencies.org/format.html#words-tokens-and-empty-nodes

            // TODO Get correct UD dep relation for relations inside the named entity
            // and for the token that must be linked to the outside. For this one, the
            // relation is the one which links to posGraphVertex to the rest of the pos
            // graph.
            auto [conllRelName, targetConllId] = getConllRelName(v);

            vertexToToken[posVertex] = tokenId;
            // std::cerr << "docFrom_analysis pushing token" << std::endl;
            first = false;
          }
          previousNeType = neType;
        }
      }
    }
    else
    {
      vertexToToken[v] = tokenId;
      tokenId++;
    }

    collectVertexDependencyInformations(v, analysis);

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

void LimaAnalyzerPrivate::collectVertexDependencyInformations(LinguisticGraphVertex v,
                                                              std::shared_ptr<Lima::AnalysisContent> analysis)
{
    auto dcurrent = syntacticData->depVertexForTokenVertex(v);
    auto depGraph = syntacticData->dependencyGraph();
    for (auto [dit, dit_end] = boost::out_edges(dcurrent, *depGraph); dit != dit_end; dit++)
    {
        auto typeMap = get(edge_deprel_type, *depGraph);
        auto type = typeMap[*dit];
        auto syntRelName = languageData->getSyntacticRelationName(type);
        auto dest = syntacticData->tokenVertexForDepVertex(
          boost::target(*dit, *depGraph));
        if (syntRelName != "")
        {
          vertexDependencyInformations.insert(std::make_pair(v, std::make_pair(dest, syntRelName)));
        }
    }
}

Doc LimaAnalyzerPrivate::docFrom_analysis(std::shared_ptr< Lima::AnalysisContent > analysis)
{
  // std::cerr << "docFrom_analysis" << std::endl;
  reset();
  auto metadataholder = std::dynamic_pointer_cast<LinguisticMetaData>(analysis->getData("LinguisticMetaData"));
  const auto& lang = metadataholder->getMetaData("Lang");
  medId = MedData::single().media(lang);
  languageData = static_cast<const LanguageData*>(&MedData::single().mediaData(medId));
  propertyCodeManager = &languageData->getPropertyCodeManager();
  propertyAccessor = &propertyCodeManager->getPropertyAccessor("MICRO");


  // std::cerr << "docFrom_analysis get stringsPool" << std::endl;
  Doc doc;
  doc.m_d->language = lang;
  doc.m_d->analysis = analysis;

  sp = &MedData::single().stringsPool(MedData::single().media(lang));


  annotationData = std::dynamic_pointer_cast<AnnotationData>(analysis->getData("AnnotationData"));
  if (annotationData == nullptr)
  {
    std::cerr << "Error: AnnotationData has not been produced: check pipeline";
    doc.m_d->error = true;
    doc.m_d->errorMessage = "Error: AnnotationData has not been produced: check pipeline";
    return doc;
  }

  auto anaGraphData = std::dynamic_pointer_cast<LinguisticAnalysisStructure::AnalysisGraph>(analysis->getData("AnalysisGraph"));
  if (anaGraphData == nullptr)
  {
    std::cerr << "Error: AnaGraph has not been produced: check pipeline";
    doc.m_d->error = true;
    doc.m_d->errorMessage = "AnaGraph: PosGraph has not been produced: check pipeline";
    return doc;
  }

  auto posGraphData = std::dynamic_pointer_cast<LinguisticAnalysisStructure::AnalysisGraph>(analysis->getData("PosGraph"));
  if (posGraphData==0)
  {
    std::cerr << "Error: PosGraph has not been produced: check pipeline";
    doc.m_d->error = true;
    doc.m_d->errorMessage = "Error: PosGraph has not been produced: check pipeline";
    return doc;
  }

  anaGraph = anaGraphData->getGraph();
  posGraph = posGraphData->getGraph();
  if (anaGraph == nullptr || posGraph == nullptr || annotationData == nullptr)
  {
    DUMPERLOGINIT;
    LERROR << "LimaAnalyzerPrivate::dumpPosGraphVertex missing data";
    doc.m_d->error = true;
    doc.m_d->errorMessage = "Error: missing data";
    return doc;
  }
  collectDependencyInformations(analysis);

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
  auto tokenId = 0;
  auto tokens = get(vertex_token, *posGraph);
  auto morphoDatas = get(vertex_data, *posGraph);

  // std::cerr << "docFrom_analysis before while" << std::endl;
  while (v != lastVertex)
  {
    // std::cerr << "docFrom_analysis on vertex " << v << posGraph << std::endl;

    dumpPosGraphVertex(doc, v, tokenId, vEndDone, "", false);

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
    auto sb = std::dynamic_pointer_cast<SegmentationData>(tmp);
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
    }
  }
  // std::cerr << "docFrom_analysis before return" << std::endl;
  return doc;
}


int LimaAnalyzerPrivate::dumpPosGraphVertex(Doc& doc,
                                            LinguisticGraphVertex v,
                                            int& tokenId,
                                            LinguisticGraphVertex vEndDone,
                                            const QString& parentNeType,
                                            bool first)
{
  // std::cerr << "LimaAnalyzerPrivate::dumpPosGraphVertex IN " << v << std::endl;
#ifdef DEBUG_LP
  DUMPERLOGINIT;
  LDEBUG << "LimaAnalyzerPrivate::dumpPosGraphVertex IN" << v;
#endif
  // vertexToToken.insert(std::make_pair(v, tokenId));
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

    auto micro = getMicro(*morphoData);
#ifdef DEBUG_LP
    LDEBUG << "LimaAnalyzerPrivate::dumpPosGraphVertex graphTag:" << micro;
#endif
    // std::cerr << "LimaAnalyzerPrivate::dumpPosGraphVertex graphTag:" << micro.toStdString() << std::endl;

    auto feats = getFeats(*morphoData);
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


#ifdef DEBUG_LP
    LDEBUG << "LimaAnalyzerPrivate::dumpPosGraphVertex conll id : " << tokenId
            << " Lima id : " << v;
#endif

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
      dumpNamedEntity(doc, v, tokenId, vEndDone, neType);
    }
    else
    {
      if (!parentNeType.isEmpty())
      {
        neType = parentNeType;
      }

      if (neType != "_")
      {
#ifdef DEBUG_LP
        LDEBUG << "LimaAnalyzerPrivate::dumpPosGraphVertex specific entity type is"
                << neType;
#endif
        neIOB = first?"B":"I";
      }

      auto [conllRelName, targetConllId] = getConllRelName(v);
      // if(!hasSpaceAfter(v, posGraph)) // TODO use hasSpaceAfter in Token
      auto features = getFeats(*morphoData);

      // std::cerr << "docFrom_analysis token/lemma are " << inflectedToken << "/" << lemmatizedToken << std::endl;

      auto pos = ft->position();
      auto len = ft->length();
      auto tStatus = ft->status().defaultKey();

      // std::cerr << "Token t: " << targetConllId << ", " << conllRelName.toStdString() << std::endl;
      Token t(len, inflectedToken, lemmatizedToken.toStdString(),
              tokenId++, pos, micro.toStdString(), targetConllId, conllRelName.toStdString(),
              features.toStdString(), neIOB.toStdString(), neType.toStdString(), tStatus.toStdString());
      // vertexToToken[v] = tokenId;
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
                                         const QString& neType)
{
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
    auto matches = annotationData->matches("PosGraph", v, "annot");
#ifdef DEBUG_LP
    LDEBUG << "LimaAnalyzerPrivate::dumpNamedEntity matches PosGraph" << v;
            // << "annot:" << matchesS(matches);
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
          dumpPosGraphVertex(doc, vse, tokenId, vEndDone, neType, first);
          first = false;
        }
#ifdef DEBUG_LP
        LDEBUG << "LimaAnalyzerPrivate::dumpNamedEntity return after SpecificEntity annotation on PosGraph";
#endif
        return;
      }
    }
    auto anaVertices = annotationData->matches("PosGraph", v, "AnalysisGraph");
#ifdef DEBUG_LP
    LDEBUG << "LimaAnalyzerPrivate::dumpNamedEntity anaVertices for" << v;
    // << ":" << matchesS(anaVertices);
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

    auto micro = getMicro(*morphoData);
#ifdef DEBUG_LP
    LDEBUG << "LimaAnalyzerPrivate::dumpAnalysisGraphVertex micro:" << micro;
#endif

    auto feats = getFeats(*morphoData);
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
    QString neIOB = first?"B-":"I-";
    auto pos = ft->position();
    auto len = ft->length();
    auto tStatus = ft->status().defaultKey();
    auto features = getFeats(*morphoData);
    auto [conllRelName, targetConllId] = getConllRelName(v);
    std::cerr << "Token t: " << targetConllId << ", " << conllRelName.toStdString() << std::endl;
    Token t(len, inflectedToken, lemmatizedToken.toStdString(), tokenId++, pos,
            micro.toStdString(), targetConllId, conllRelName.toStdString(), features.toStdString(),
            neIOB.toStdString(), neType.toStdString(), tStatus.toStdString());

    // vertexToToken[v] = tokenId;
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
    // std::cerr << "LimaAnalyzerPrivate::getNeType call matches with " << "PosGraph"
    //     << " and " << posGraphVertex << std::endl;
    auto matches = annotationData->matches("PosGraph", posGraphVertex, "annot");
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
      auto anaVertices = annotationData->matches("PosGraph", posGraphVertex, "AnalysisGraph");
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

std::pair<QString, int> LimaAnalyzerPrivate::getConllRelName(LinguisticGraphVertex v)
{
#ifdef DEBUG_LP
  DUMPERLOGINIT;
  LDEBUG << "LimaAnalyzerPrivate::getConllRelName" << v << vertexDependencyInformations.count(v);
#endif
  QString conllRelName = "_";
  int targetConllId = 0;
  if (vertexDependencyInformations.count(v) != 0)
  {
    auto target = vertexDependencyInformations.find(v)->second.first;
#ifdef DEBUG_LP
    LDEBUG << "LimaAnalyzerPrivate::getConllRelName target saved for" << v << "is" << target;
#endif
    if (vertexToToken.find(target) != vertexToToken.end())
    {
      targetConllId =  vertexToToken.find(target)->second;
    }
    else
    {
      DUMPERLOGINIT;
      LERROR << "LimaAnalyzerPrivate::getConllRelName target" << target << "not found in segmentation mapping";
    }
#ifdef DEBUG_LP
    LDEBUG << "LimaAnalyzerPrivate::getConllRelName conll target saved for " << v << " is " << targetConllId;
#endif
    auto relName = QString::fromStdString(vertexDependencyInformations.find(v)->second.second);
#ifdef DEBUG_LP
    LDEBUG << "LimaAnalyzerPrivate::getConllRelName the lima dependency tag for " << v << " is " << relName;
#endif
    if (conllLimaDepMapping.contains(relName))
    {
      conllRelName = conllLimaDepMapping[relName];
    }
    else
    {
      conllRelName = relName;
//             LERROR << "LimaAnalyzerPrivate::getConllRelName" << relName << "not found in mapping";
    }

    // There is no way for vertex to have 0 as head.
    if (conllRelName == "root")
    {
      targetConllId = 0;
    }
  }
  else
  {
#ifdef DEBUG_LP
    LDEBUG << "LimaAnalyzerPrivate::getConllRelName no target saved for" << v;
#endif
  }
#ifdef DEBUG_LP
    LDEBUG << "LimaAnalyzerPrivate::getConllRelName result for" << v << "is" << conllRelName << targetConllId;
#endif
  return { conllRelName, targetConllId };
}

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

QString LimaAnalyzerPrivate::getMicro(LinguisticAnalysisStructure::MorphoSyntacticData& morphoData)
{
  return QString::fromUtf8(static_cast<const LangData&>(
      MedData::single().mediaData(medId)).getPropertyCodeManager()
        .getPropertyManager("MICRO")
        .getPropertySymbolicValue(morphoData.firstValue(
          *propertyAccessor)).c_str());
}

std::map<std::string, std::string> LimaAnalyzerPrivate::parseMetaData(
  const QString& meta,
  QChar comma,
  QChar colon,
  const std::map<std::string, std::string>& append)
{
  std::map<std::string, std::string> opts;
  auto metaView = QStringView(meta);
  auto metas = metaView.split(comma, Qt::SkipEmptyParts);
  for (const auto& keyValueString: metas)
  {
    auto kv = keyValueString.split(colon, Qt::SkipEmptyParts);
    if (kv.size()!= 2)
    {
      DUMPERLOGINIT;
      LERROR << "Error in metadata string. Cannot split" << keyValueString << "in key/value pair on" << colon;
    }
    else
    {
      opts[kv[0].toString().toStdString()] = kv[1].toString().toStdString();
    }
  }
  return opts;
}
